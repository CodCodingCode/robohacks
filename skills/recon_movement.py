"""Bounded recon movement skill for natural-language Innate agents."""

from __future__ import annotations

import math
import re
import threading
import time
from typing import Callable


# ---------------------------------------------------------------------------
# LiDAR forward-clearance cache
# ---------------------------------------------------------------------------
# The skills_action_server runs inside a live rclpy context.  We subscribe
# to /scan here at module load time so all ReconMovementSkill instances share
# a single cached forward-clearance reading.  Falls back silently when rclpy
# or the /scan topic is unavailable.

_scan_lock = threading.Lock()
_min_forward_m: float | None = None  # latest minimum range in forward arc
_scan_node = None                     # rclpy node used only for this sub

def _try_start_scan_subscriber() -> None:
    """Create a minimal rclpy node to listen to /scan.  Idempotent."""
    global _scan_node
    if _scan_node is not None:
        return
    try:
        import rclpy                              # noqa: PLC0415
        from sensor_msgs.msg import LaserScan     # noqa: PLC0415

        if not rclpy.ok():
            return

        node = rclpy.create_node("recon_movement_scan_listener")
        _FORWARD_ARC = math.pi / 12  # ±15° narrow forward cone

        def _scan_cb(msg: LaserScan) -> None:
            global _min_forward_m
            try:
                n = len(msg.ranges)
                if n == 0:
                    return
                half = int(_FORWARD_ARC / msg.angle_increment) if msg.angle_increment > 0 else n // 12
                center = n // 2
                lo, hi = max(0, center - half), min(n, center + half + 1)
                vals = [
                    r for r in msg.ranges[lo:hi]
                    if msg.range_min < r < msg.range_max and math.isfinite(r)
                ]
                with _scan_lock:
                    _min_forward_m = min(vals) if vals else None
            except Exception:
                pass

        node.create_subscription(LaserScan, "/scan", _scan_cb, 10)
        # Spin in a daemon thread so it doesn't block the skill executor.
        t = threading.Thread(
            target=lambda: rclpy.spin(node),
            daemon=True,
            name="recon_scan_spin",
        )
        t.start()
        _scan_node = node
    except Exception:
        pass  # rclpy unavailable (offline tests, etc.)


def _get_min_forward_m() -> float | None:
    """Return the latest minimum forward range in metres, or None."""
    _try_start_scan_subscriber()
    with _scan_lock:
        return _min_forward_m


_OBSTACLE_STOP_M = 0.35   # stop driving if obstacle closer than this in narrow arc


# ---------------------------------------------------------------------------
# Shared VLM annotations cache (published by map_stream_node)
# ---------------------------------------------------------------------------
# map_stream_node publishes /recon/vlm_annotations (latched) after every
# Gemini call.  We subscribe once at module load and keep the latest result
# so approach_object can use the already-computed annotations on its first
# iteration instead of making a blocking 3-second Gemini call.

_vlm_cache_lock = threading.Lock()
_vlm_cache: dict = {}          # {"annotations": [...], "ts": float}
_vlm_cache_node = None

def _try_start_vlm_cache_subscriber() -> None:
    global _vlm_cache_node
    if _vlm_cache_node is not None:
        return
    try:
        import json as _json                     # noqa: PLC0415
        import rclpy                             # noqa: PLC0415
        from std_msgs.msg import String          # noqa: PLC0415
        from rclpy.qos import (                  # noqa: PLC0415
            QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy,
        )

        if not rclpy.ok():
            return

        node = rclpy.create_node("recon_movement_vlm_cache")
        qos = QoSProfile(
            depth=1,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
        )

        def _cb(msg: String) -> None:
            try:
                data = _json.loads(msg.data)
                with _vlm_cache_lock:
                    _vlm_cache.update(data)
            except Exception:
                pass

        node.create_subscription(String, "/recon/vlm_annotations", _cb, qos)
        t = threading.Thread(
            target=lambda: rclpy.spin(node),
            daemon=True,
            name="recon_vlm_cache_spin",
        )
        t.start()
        _vlm_cache_node = node
    except Exception:
        pass


def _get_cached_annotations(max_age_s: float = 4.0) -> list | None:
    """Return pre-computed VLM annotations if fresh enough, else None."""
    _try_start_vlm_cache_subscriber()
    with _vlm_cache_lock:
        ts = _vlm_cache.get("ts", 0.0)
        if time.time() - ts <= max_age_s:
            return list(_vlm_cache.get("annotations", []))
    return None

from vlm.planner import Planner, RobotCommand, bbox_to_bearing

try:
    from brain_client.skill_types import (
        Interface,
        InterfaceType,
        RobotState,
        RobotStateType,
        Skill,
        SkillResult,
    )
except ImportError:  # pragma: no cover - only used for offline imports/tests.
    class Skill:  # type: ignore[no-redef]
        """Minimal fallback so this module can be imported off-robot."""

    class SkillResult:  # type: ignore[no-redef]
        SUCCESS = "success"
        FAILURE = "failure"
        CANCELLED = "cancelled"

    class InterfaceType:  # type: ignore[no-redef]
        MOBILITY = "mobility"

    class Interface:  # type: ignore[no-redef]
        def __init__(self, _interface_type):
            self.interface_type = _interface_type
            self.name = ""

        def __set_name__(self, _owner, name):
            self.name = name

        def __get__(self, instance, _owner=None):
            if instance is None:
                return self
            return instance.__dict__.get(self.name)

        def __set__(self, instance, value):
            instance.__dict__[self.name] = value

    class RobotStateType:  # type: ignore[no-redef]
        LAST_MAIN_CAMERA_IMAGE_B64 = "last_main_camera_image_b64"

    class RobotState:  # type: ignore[no-redef]
        def __init__(self, _state_type):
            self.state_type = _state_type
            self.name = ""

        def __set_name__(self, _owner, name):
            self.name = name

        def __get__(self, instance, _owner=None):
            if instance is None:
                return self
            return instance.__dict__.get(self.name)

        def __set__(self, instance, value):
            instance.__dict__[self.name] = value


Analyzer = Callable[[str], dict]
Sleeper = Callable[[float], None]

SUPPORTED_ACTIONS = {
    "scan_room",
    "move_forward",
    "approach_detected_threat",
    "approach_object",
    "hold",
    "reset_recon",
    "rotate",       # turn by angle: distance_m = degrees (+ left/CCW, - right/CW)
    "find_object",  # spin until target found, then approach
    "move_left",    # rotate left, drive forward, rotate back
    "move_right",   # rotate right, drive forward, rotate back
}

MAX_FORWARD_SPEED_MPS = 0.20
MAX_ANGULAR_SPEED_RADPS = 0.60
MAX_FORWARD_DISTANCE_M = 5.00
MAX_COMMAND_DURATION_S = 12.00
MAX_APPROACH_DURATION_S = 90.00
SEARCH_SPIN_SPEED_RADPS = 0.25
SCAN_STEPS = 8


class ReconMovementSkill(Skill):
    """Translate high-level recon intents into bounded mobility commands."""

    mobility = Interface(InterfaceType.MOBILITY)
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)

    def __init__(
        self,
        *args,
        analyzer: Analyzer | None = None,
        planner: Planner | None = None,
        sleeper: Sleeper = time.sleep,
        **kwargs,
    ) -> None:
        try:
            super().__init__(*args, **kwargs)
        except TypeError:
            try:
                import logging
                super().__init__(logger=logging.getLogger("recon_movement"))
            except TypeError:
                pass
        self._analyzer = analyzer
        self._planner = planner or Planner()
        self._sleep = sleeper
        self._cancelled = False

    @property
    def name(self) -> str:
        return "recon_movement"

    def guidelines(self) -> str:
        return (
            "Use for bounded recon movement only: scan_room, move_forward, "
            "move_left, move_right, approach_detected_threat, approach_object, "
            "hold, or reset_recon."
        )

    def execute(
        self,
        action: str,
        target: str = "",
        distance_m: float = 0.5,
        max_duration_s: float = 20.0,
    ):
        self._cancelled = False
        action = _normalize_action(action)
        if action not in SUPPORTED_ACTIONS:
            return (
                f"Unsupported recon action: {action or 'empty'}",
                SkillResult.FAILURE,
            )

        if action == "hold":
            self._stop()
            return "Holding position", SkillResult.SUCCESS
        if action == "reset_recon":
            self._planner.reset()
            self._stop()
            return "Recon planner reset", SkillResult.SUCCESS
        if action == "scan_room":
            return self._scan_room()
        if action == "move_forward":
            return self._move_forward(distance_m, max_duration_s)
        if action == "move_left":
            return self._move_lateral(
                direction=1,
                distance_m=distance_m,
                max_duration_s=max_duration_s,
            )
        if action == "move_right":
            return self._move_lateral(
                direction=-1,
                distance_m=distance_m,
                max_duration_s=max_duration_s,
            )
        if action == "approach_object":
            return self._approach_object(target, max_duration_s)
        if action == "rotate":
            # distance_m is repurposed as degrees; positive = left/CCW, negative = right/CW
            degrees = _coerce_float(distance_m, default=90.0)
            return self._rotate_by(math.radians(degrees))
        if action == "find_object":
            return self._find_and_approach(target, max_duration_s)
        return self._approach_detected_threat(max_duration_s)

    def cancel(self):
        self._cancelled = True
        self._stop()
        return "Recon movement cancelled"

    def _scan_room(self):
        self._require_mobility()
        step = (2.0 * math.pi) / SCAN_STEPS
        step_duration = step / MAX_ANGULAR_SPEED_RADPS
        for idx in range(SCAN_STEPS):
            if self._cancelled:
                self._stop()
                return "Scan cancelled", SkillResult.CANCELLED
            self._feedback(f"Scanning direction {idx + 1}/{SCAN_STEPS}")
            self.mobility.send_cmd_vel(0.0, MAX_ANGULAR_SPEED_RADPS, step_duration)
            self._sleep(step_duration)
        self._stop()
        return "Room scan complete", SkillResult.SUCCESS

    def _move_forward(self, distance_m: float, max_duration_s: float):
        self._require_mobility()
        distance = _coerce_float(distance_m, default=0.5)
        if distance <= 0.0:
            return "distance_m must be positive", SkillResult.FAILURE
        distance = min(distance, MAX_FORWARD_DISTANCE_M)
        max_duration = _clamp_duration(max_duration_s, default=20.0)
        duration = min(distance / MAX_FORWARD_SPEED_MPS, max_duration)
        return self._drive_for(
            linear_x=MAX_FORWARD_SPEED_MPS,
            angular_z=0.0,
            duration_s=duration,
            success_message=f"Issued forward movement for up to {distance:.2f}m",
        )

    def _move_lateral(self, direction: int, distance_m: float, max_duration_s: float):
        """Approximate a lateral step by turning 90 deg, driving, then turning back."""
        self._require_mobility()
        distance = _coerce_float(distance_m, default=0.5)
        if distance <= 0.0:
            return "distance_m must be positive", SkillResult.FAILURE
        distance = min(distance, MAX_FORWARD_DISTANCE_M)
        max_duration = min(
            _clamp_duration(max_duration_s, default=20.0),
            MAX_APPROACH_DURATION_S,
        )
        turn_sign = 1 if direction >= 0 else -1
        label = "left" if turn_sign > 0 else "right"
        turn_duration = (math.pi / 2.0) / MAX_ANGULAR_SPEED_RADPS
        drive_duration = distance / MAX_FORWARD_SPEED_MPS
        steps = (
            (0.0, turn_sign * MAX_ANGULAR_SPEED_RADPS, turn_duration),
            (MAX_FORWARD_SPEED_MPS, 0.0, drive_duration),
            (0.0, -turn_sign * MAX_ANGULAR_SPEED_RADPS, turn_duration),
        )

        remaining = max_duration
        for linear_x, angular_z, duration in steps:
            segment_remaining = duration
            while segment_remaining > 0.0 and remaining > 0.0:
                if self._cancelled:
                    self._stop()
                    return f"Move {label} cancelled", SkillResult.CANCELLED
                chunk = min(segment_remaining, remaining, MAX_COMMAND_DURATION_S)
                self.mobility.send_cmd_vel(linear_x, angular_z, chunk)
                self._sleep(chunk)
                segment_remaining -= chunk
                remaining -= chunk

        self._stop()
        return f"Issued {label} movement for up to {distance:.2f}m", SkillResult.SUCCESS

    def _approach_detected_threat(self, max_duration_s: float):
        self._require_mobility()
        max_duration = min(
            _clamp_duration(max_duration_s, default=60.0),
            MAX_APPROACH_DURATION_S,
        )
        return self._approach_with_think_fast_slow(
            target="threat",
            max_duration=max_duration,
            get_annotation=lambda result: self._planner._find_priority_target(result),
        )

    def _approach_object(self, target: str, max_duration_s: float):
        self._require_mobility()
        target = str(target or "").strip()
        if not target:
            self._stop()
            return "approach_object requires a target", SkillResult.FAILURE

        max_duration = min(
            _clamp_duration(max_duration_s, default=60.0),
            MAX_APPROACH_DURATION_S,
        )
        return self._approach_with_think_fast_slow(
            target=target,
            max_duration=max_duration,
            get_annotation=lambda result: _find_target_annotation(
                result.get("annotations", []), target
            ),
        )

    def _rotate_by(self, angle_rad: float):
        """Rotate in place by the given angle (radians). + = CCW/left, - = CW/right."""
        self._require_mobility()
        angle_rad = _clamp(angle_rad, -2.0 * math.pi, 2.0 * math.pi)
        if abs(angle_rad) < 1e-3:
            return "No rotation needed", SkillResult.SUCCESS
        duration = min(abs(angle_rad) / MAX_ANGULAR_SPEED_RADPS, MAX_APPROACH_DURATION_S)
        angular_z = math.copysign(MAX_ANGULAR_SPEED_RADPS, angle_rad)
        self.mobility.send_cmd_vel(0.0, angular_z, duration)
        self._sleep(duration)
        self._stop()
        deg = math.degrees(angle_rad)
        return f"Rotated {deg:+.0f}°", SkillResult.SUCCESS

    def _find_and_approach(self, target: str, max_duration_s: float):
        """Spin until the target is visible via VLM, then approach it.

        Uses the think-fast/think-slow loop once the object is found.
        Calls VLM every ~2s during the search spin.
        """
        self._require_mobility()
        target = str(target or "").strip()
        if not target:
            return "find_object requires a target", SkillResult.FAILURE

        max_duration = min(
            _clamp_duration(max_duration_s, default=60.0),
            MAX_APPROACH_DURATION_S,
        )
        remaining = max_duration

        # How long to spin between VLM checks during the search phase.
        SEARCH_STEP_S = 1.5

        self._feedback(f"Searching for {target}…")

        while remaining > 0.0:
            if self._cancelled:
                self._stop()
                return f"Search for {target} cancelled", SkillResult.CANCELLED

            # Think Slow: check if target is visible.
            # Prefer cached annotations from the background VLM thread to
            # avoid blocking the search loop with synchronous Gemini calls.
            cached = _get_cached_annotations(max_age_s=8.0)
            if cached is not None:
                result = {"annotations": cached}
            else:
                # Cold start fallback: cache never populated yet.
                image_b64 = self.image
                if not image_b64:
                    self._stop()
                    return f"No camera frame available to search for {target}", SkillResult.FAILURE
                result = self._analyze_frame(image_b64)
            annotation = _find_target_annotation(result.get("annotations", []), target)

            if annotation is not None:
                self._feedback(f"Found {target} — approaching")
                # Hand off to the full think-fast/think-slow approach.
                return self._approach_with_think_fast_slow(
                    target=target,
                    max_duration=remaining,
                    get_annotation=lambda r: _find_target_annotation(
                        r.get("annotations", []), target
                    ),
                )

            # Not found yet — spin and try again.
            spin_dur = min(SEARCH_STEP_S, remaining)
            self.mobility.send_cmd_vel(0.0, SEARCH_SPIN_SPEED_RADPS, spin_dur)
            self._sleep(spin_dur)
            remaining -= spin_dur

        self._stop()
        return f"Could not find {target} after full search", SkillResult.FAILURE

    def _approach_with_think_fast_slow(
        self,
        target: str,
        max_duration: float,
        get_annotation,
    ):
        """Think-fast / think-slow approach loop.

        Think Slow (VLM): Gemini call to locate the target, measure bearing
            and approximate distance (via bbox size proxy).  Only called after
            a search spin or after completing a burst of drive steps.

        Think Fast (P-controller + adaptive burst):
            • angular_z = -Kp × bearing (bbox bearing is positive to the right)
            • forward speed scaled down when bearing is large (pointing away)
            • burst duration capped to estimated remaining distance so the
              robot does not overshoot
            • angular correction decays across bursts (first burst corrects,
              later bursts drive straighter)
        """
        # P-controller gain. bbox_to_bearing returns positive for targets to
        # the right in image space; cmd_vel.angular_z is positive left/CCW.
        Kp = 1.4
        # How many drive steps between VLM re-checks
        DRIVE_BURSTS = 3

        remaining = max_duration

        while remaining > 0.0:
            if self._cancelled:
                self._stop()
                return f"Approach to {target} cancelled", SkillResult.CANCELLED

            # ── THINK SLOW: perception frame ──────────────────────────────
            # Always prefer cached annotations from the background VLM thread
            # (published every ~2s to /recon/vlm_annotations) to avoid
            # blocking the approach loop with synchronous Gemini calls.
            cached = _get_cached_annotations(max_age_s=8.0)
            if cached is not None:
                result = {"annotations": cached}
            else:
                # Cold start fallback: cache never populated yet.
                image_b64 = self.image
                if not image_b64:
                    self._stop()
                    return f"No camera frame available to approach {target}", SkillResult.FAILURE
                result = self._analyze_frame(image_b64)

            annotation = get_annotation(result)

            if annotation is None:
                self._feedback(f"Searching for {target}")
                dur = min(1.5, remaining)
                self.mobility.send_cmd_vel(0.0, SEARCH_SPIN_SPEED_RADPS, dur)
                self._sleep(dur)
                remaining -= dur
                continue

            bbox = annotation.get("bbox")
            if not _valid_bbox(bbox):
                remaining -= 0.2
                continue

            bearing, size_proxy = bbox_to_bearing(bbox)

            # ── Arrival check ─────────────────────────────────────────────
            if size_proxy >= self._planner.CLOSE_ENOUGH:
                self._stop()
                label = annotation.get("label", target)
                return f"Arrived near {label}", SkillResult.SUCCESS

            # ── Adaptive burst duration from size proxy ───────────────────
            # size_proxy ≈ CLOSE_ENOUGH at CLOSE_ENOUGH_M distance, so:
            # estimated_dist ≈ CLOSE_ENOUGH_M × sqrt(CLOSE_ENOUGH / size_proxy)
            if size_proxy > 0.01:
                estimated_dist = self._planner.CLOSE_ENOUGH_M * math.sqrt(
                    self._planner.CLOSE_ENOUGH / max(size_proxy, 0.01)
                )
            else:
                estimated_dist = self._planner.CLOSE_ENOUGH_M * 3.0  # far away

            # ── THINK FAST: P-controller curved approach ──────────────────
            # Compute initial angular correction proportional to bearing error.
            angular_z_full = _bearing_to_angular_z(bearing, gain=Kp)
            # Scale down forward speed when bearing is large (robot is sideways).
            # Minimum 40% speed so robot keeps moving while correcting.
            forward_scale = max(0.4, 1.0 - abs(bearing) / (math.pi / 3.0))
            linear_x = self._planner.APPROACH_SPEED * forward_scale

            # Cap burst to 60% of estimated remaining distance to avoid overshoot.
            single_burst = min(
                self._planner.APPROACH_DURATION,
                max(0.5, estimated_dist / max(linear_x, 0.05) * 0.6),
                remaining,
            )

            self._feedback(
                f"Approaching {target} "
                f"(bearing={bearing:+.2f} dist≈{estimated_dist:.1f}m)"
            )

            for i in range(DRIVE_BURSTS):
                if self._cancelled or remaining <= 0.0:
                    break
                # LiDAR obstacle check before each burst.
                fwd = _get_min_forward_m()
                if fwd is not None and fwd < _OBSTACLE_STOP_M:
                    self._stop()
                    self._feedback(f"Obstacle {fwd:.2f}m ahead — stopping")
                    return f"Obstacle blocked approach to {target}", SkillResult.FAILURE
                # Angular correction decays: full on burst 0, 30% from burst 1 onwards.
                # After the first corrective burst the robot should be aligned;
                # later bursts drive mostly straight.
                az = angular_z_full if i == 0 else angular_z_full * 0.3
                dur = min(single_burst, remaining)
                self.mobility.send_cmd_vel(linear_x, az, dur)
                self._sleep(dur)
                remaining -= dur

        self._stop()
        return f"Could not reach {target}; holding position", SkillResult.FAILURE

    def _object_command(self, annotation: dict, target: str) -> RobotCommand:
        bbox = annotation.get("bbox")
        if not _valid_bbox(bbox):
            return RobotCommand(
                kind="wait",
                duration=0.5,
                reason=f"Waiting for a valid bounding box for {target}",
            )

        bearing, size_proxy = bbox_to_bearing(bbox)
        label = annotation.get("label") or target
        if abs(bearing) > self._planner.BEARING_TOLERANCE:
            return RobotCommand(
                kind="rotate",
                angle=bearing,
                reason=f"Centering on {label} (bearing={bearing:+.2f} rad)",
            )
        if size_proxy < self._planner.CLOSE_ENOUGH:
            return RobotCommand(
                kind="cmd_vel",
                linear_x=self._planner.APPROACH_SPEED,
                duration=self._planner.APPROACH_DURATION,
                reason=f"Approaching {label} (size={size_proxy:.3f})",
            )
        return RobotCommand(
            kind="done",
            reason=f"At {label} (size={size_proxy:.3f})",
        )

    def _analyze_frame(self, image_b64: str) -> dict:
        if self._analyzer is not None:
            return self._analyzer(image_b64)
        from vlm.analyze import analyze_frame

        return analyze_frame(image_b64, phase="recon")

    def _run_planner_command(self, command: RobotCommand):
        self._feedback(command.reason)
        if command.kind == "done":
            return SkillResult.SUCCESS, 0.0
        if command.kind == "wait":
            duration = min(
                _clamp_duration(command.duration, default=1.0),
                MAX_COMMAND_DURATION_S,
            )
            self._sleep(duration)
            return None, max(duration, 0.1)
        if command.kind == "rotate":
            angle = _clamp(command.angle, -math.pi / 2.0, math.pi / 2.0)
            if abs(angle) > 1e-3:
                duration = min(abs(angle) / MAX_ANGULAR_SPEED_RADPS, MAX_COMMAND_DURATION_S)
                angular_z = math.copysign(MAX_ANGULAR_SPEED_RADPS, angle)
                self.mobility.send_cmd_vel(0.0, angular_z, duration)
                self._sleep(duration)
            return None, max(abs(angle) / MAX_ANGULAR_SPEED_RADPS, 0.1)
        if command.kind == "cmd_vel":
            linear_x = _clamp(
                command.linear_x,
                -MAX_FORWARD_SPEED_MPS,
                MAX_FORWARD_SPEED_MPS,
            )
            angular_z = _clamp(
                command.angular_z,
                -MAX_ANGULAR_SPEED_RADPS,
                MAX_ANGULAR_SPEED_RADPS,
            )
            duration = min(
                _clamp_duration(command.duration, default=1.0),
                MAX_COMMAND_DURATION_S,
            )
            self.mobility.send_cmd_vel(linear_x, angular_z, duration)
            self._sleep(duration)
            return None, max(duration, 0.1)
        return SkillResult.FAILURE, 0.0

    def _drive_for(
        self,
        linear_x: float,
        angular_z: float,
        duration_s: float,
        success_message: str,
    ):
        remaining = min(duration_s, MAX_APPROACH_DURATION_S)
        while remaining > 0.0:
            if self._cancelled:
                self._stop()
                return "Movement cancelled", SkillResult.CANCELLED
            chunk = min(remaining, MAX_COMMAND_DURATION_S)
            self.mobility.send_cmd_vel(linear_x, angular_z, chunk)
            self._sleep(chunk)
            remaining -= chunk
        self._stop()
        return success_message, SkillResult.SUCCESS

    def _stop(self) -> None:
        try:
            self.mobility.send_cmd_vel(0.0, 0.0, 0.1)
        except Exception:
            pass

    def _require_mobility(self) -> None:
        if getattr(self, "mobility", None) is None:
            raise RuntimeError("MobilityInterface is not available")

    def _feedback(self, message: str) -> None:
        if not message:
            return
        sender = getattr(self, "_send_feedback", None)
        if callable(sender):
            sender(message)


def _normalize_action(action: str) -> str:
    return str(action or "").strip().lower().replace("-", "_").replace(" ", "_")


def _find_target_annotation(annotations: list, target: str) -> dict | None:
    scored = [
        (_target_score(annotation.get("label", ""), target), annotation)
        for annotation in annotations
        if isinstance(annotation, dict)
    ]
    scored = [(score, annotation) for score, annotation in scored if score > 0]
    if not scored:
        return None
    return max(scored, key=lambda item: (item[0], _bbox_area(item[1].get("bbox"))))[1]


def _target_score(label: str, target: str) -> int:
    label_norm = _normalize_match_text(label)
    target_norm = _normalize_match_text(target)
    if not label_norm or not target_norm:
        return 0
    if target_norm in label_norm:
        return 4
    if label_norm in target_norm:
        return 3

    label_tokens = set(label_norm.split())
    target_tokens = set(target_norm.split())
    if target_tokens and target_tokens.issubset(label_tokens):
        return 3
    if label_tokens and label_tokens.issubset(target_tokens):
        return 2
    if label_tokens & target_tokens:
        return 1
    return 0


def _normalize_match_text(value: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", str(value).lower())
    normalized = []
    for token in tokens:
        if len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        if token not in {"a", "an", "the", "of", "to"}:
            normalized.append(token)
    return " ".join(normalized)


def _valid_bbox(bbox) -> bool:
    return (
        isinstance(bbox, list)
        and len(bbox) == 4
        and all(isinstance(v, (int, float)) for v in bbox)
        and bbox[2] > bbox[0]
        and bbox[3] > bbox[1]
    )


def _bbox_area(bbox) -> float:
    if not _valid_bbox(bbox):
        return 0.0
    return float((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))


def _bearing_to_angular_z(bearing: float, gain: float = 1.0) -> float:
    """Convert image-space bearing to cmd_vel angular velocity."""
    return _clamp(-gain * bearing, -MAX_ANGULAR_SPEED_RADPS, MAX_ANGULAR_SPEED_RADPS)


def _coerce_float(value: float, default: float) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(out):
        return default
    return out


def _clamp_duration(value: float, default: float) -> float:
    return _clamp(_coerce_float(value, default), 0.1, MAX_APPROACH_DURATION_S)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
