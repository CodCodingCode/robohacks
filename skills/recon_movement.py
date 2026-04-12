"""Bounded recon movement skill for natural-language Innate agents."""

from __future__ import annotations

import math
import re
import time
from typing import Callable

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
            "approach_detected_threat, approach_object, hold, or reset_recon."
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
        if action == "approach_object":
            return self._approach_object(target, max_duration_s)
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

    def _approach_detected_threat(self, max_duration_s: float):
        self._require_mobility()
        max_duration = min(
            _clamp_duration(max_duration_s, default=20.0),
            MAX_APPROACH_DURATION_S,
        )
        remaining = max_duration

        while remaining > 0.0:
            if self._cancelled:
                self._stop()
                return "Approach cancelled", SkillResult.CANCELLED

            image_b64 = self.image
            if not image_b64:
                self._stop()
                return "No camera frame available for threat approach", SkillResult.FAILURE

            result = self._analyze_frame(image_b64)
            command = self._planner.next_command(result)
            outcome, budget = self._run_planner_command(command)

            if outcome == SkillResult.SUCCESS:
                self._stop()
                return command.reason or "Approach complete", SkillResult.SUCCESS
            if outcome == SkillResult.FAILURE:
                self._stop()
                return command.reason or "Planner command failed", SkillResult.FAILURE

            remaining -= budget

        self._stop()
        return "Approach timed out; holding position", SkillResult.FAILURE

    def _approach_object(self, target: str, max_duration_s: float):
        self._require_mobility()
        target = str(target or "").strip()
        if not target:
            self._stop()
            return "approach_object requires a target", SkillResult.FAILURE

        max_duration = min(
            _clamp_duration(max_duration_s, default=20.0),
            MAX_APPROACH_DURATION_S,
        )
        remaining = max_duration

        while remaining > 0.0:
            if self._cancelled:
                self._stop()
                return f"Approach to {target} cancelled", SkillResult.CANCELLED

            image_b64 = self.image
            if not image_b64:
                self._stop()
                return f"No camera frame available to approach {target}", SkillResult.FAILURE

            result = self._analyze_frame(image_b64)
            annotation = _find_target_annotation(
                result.get("annotations", []),
                target,
            )
            if annotation is None:
                command = RobotCommand(
                    kind="cmd_vel",
                    angular_z=SEARCH_SPIN_SPEED_RADPS,
                    duration=1.0,
                    reason=f"Searching for {target}",
                )
            else:
                command = self._object_command(annotation, target)

            outcome, budget = self._run_planner_command(command)
            if outcome == SkillResult.SUCCESS:
                self._stop()
                return command.reason or f"Arrived near {target}", SkillResult.SUCCESS
            if outcome == SkillResult.FAILURE:
                self._stop()
                return command.reason or f"Could not approach {target}", SkillResult.FAILURE

            remaining -= budget

        self._stop()
        return f"Could not find or reach {target}; holding position", SkillResult.FAILURE

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
