#!/usr/bin/env python3
"""Standalone SLAM → dashboard WebSocket bridge with intruder alerts.

Runs as a plain ROS2 Python node (NOT a brain_client Skill). Subscribes
directly to /odom and /map and streams JSON frames over a WebSocket.

Intruder alert: when ELEVENLABS_API_KEY is set alongside GEMINI_API_KEY,
the VLM thread automatically detects people in camera frames and plays
a spoken warning through the robot speakers via the ElevenLabs TTS API.

Why standalone instead of the MapStreamSkill approach: the brain_client
skills_action_server runs on a single-threaded rclpy executor, so during
a long-running Skill.execute() call, no subscription callbacks fire —
meaning /odom and /map are never seen. A standalone node with its own
executor doesn't have that problem.

Usage (on the Jetson, after sourcing ROS + workspace):

    export GEMINI_API_KEY=your-gemini-key
    export ELEVENLABS_API_KEY=your-elevenlabs-key   # enables intruder alerts
    python3 slam/map_stream_node.py --host 0.0.0.0 --port 8080

Then open http://<robot-ip>:8080/ — static dashboard + WebSocket JSON on /ws.

The JSON shape matches dashboard/app.js applyState() (shallow merge):

    {
      "timestamp": float,
      "mission_phase": "recon",
      "robot": {"x", "y", "theta", "battery"},
      "slam": {"map": {"width", "height", "resolution", "origin": {"x","y"}, "data": [...]}}
    }
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import mimetypes
import sys
import threading
import time
from pathlib import Path

# Make the `vlm` and `slam` packages importable regardless of the current
# working directory the launcher was started from. Without this, running the
# node from e.g. /home/jetson1 instead of /home/jetson1/robohacks causes
# `import vlm` to fail silently and the intel panel stays blank.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid, Odometry
from sensor_msgs.msg import BatteryState, CameraInfo, Image, LaserScan
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
try:
    from slam.depth_fusion import (
        camera_info_to_dict,
        decode_depth_image,
        markers_from_annotations,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - script execution fallback.
    if exc.name != "slam":
        raise
    from depth_fusion import (
        camera_info_to_dict,
        decode_depth_image,
        markers_from_annotations,
    )

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"
DEFAULT_DEPTH_TOPIC = "/mars/main_camera/depth/image_rect_raw"
DEFAULT_CAMERA_INFO_TOPIC = "/mars/main_camera/left/camera_info"

POSE_HZ = 10.0
MAP_HZ = 1.0
# LiDAR fallback when /map is empty (large messages — keep slow).
SCAN_HZ = 0.5
# VLM analysis cadence — Gemini rate limit is 2s minimum.
VLM_INTERVAL = 3.0
SEMANTIC_MARKER_TTL = 8.0
AUTONOMY_SWITCHING_ENABLED = False


def _yaw_from_quat(qx: float, qy: float, qz: float, qw: float) -> float:
    return math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))


class MapStreamNode(Node):
    """Tracks the latest robot pose (from whichever pose topic wins) and map."""

    def __init__(
        self,
        depth_topic: str = "",
        camera_info_topic: str = "",
        depth_scale: float = 0.001,
    ) -> None:
        super().__init__("map_stream_node")
        self._lock = threading.Lock()
        # Store pose as a normalized (x, y, theta) tuple regardless of which
        # topic it came from. `None` until we see our first frame.
        self._pose: tuple[float, float, float] | None = None
        self._last_map: OccupancyGrid | None = None
        self._last_scan: LaserScan | None = None
        self._battery_pct: float | None = None
        # Latest compressed camera frame (bytes) for VLM analysis.
        self._last_image_bytes: bytes | None = None
        # Encode queue: _image_cb drops raw numpy frames here; _encode_loop
        # compresses them off the ROS spin thread so /odom and /map callbacks
        # are never blocked by cv2.imencode().
        import queue as _queue_mod
        self._encode_queue: _queue_mod.Queue = _queue_mod.Queue(maxsize=1)
        self._encode_thread = threading.Thread(
            target=self._encode_loop, daemon=True
        )
        self._encode_thread.start()
        self._last_depth_m = None
        self._camera_info: dict | None = None
        self._depth_scale = depth_scale
        # Latest VLM result — merged into every broadcaster payload.
        self._vlm_result: dict = {}
        self._vlm_result_ts: float = 0.0
        # Semantic marker cache — recomputed only when _vlm_result_ts changes.
        self._cached_markers: list = []
        self._cached_markers_ts: float = 0.0
        # Autonomy: operator-controlled toggle for planner execution.
        self._autonomy_enabled: bool = False
        self._pending_cmd: dict = {}  # {"kind": str, "reason": str}
        # Planner phase — synced by run_planner_thread so run_vlm_thread can
        # switch Gemini prompts without direct access to the Planner object.
        self._planner_phase: str = "recon"
        # One-shot alert: set when autonomy auto-disables on "done", cleared on read.
        self._alert: str | None = None
        self._manual_motion_token: int = 0

        # /cmd_vel publisher — used by the planner thread when autonomy is on.
        from geometry_msgs.msg import Twist  # noqa: PLC0415
        from std_msgs.msg import String  # noqa: PLC0415
        self._cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        # /defusal_action publisher — operator wire-cut / switch commands.
        self._defusal_action_pub = self.create_publisher(String, "/defusal_action", 10)

        # Pose sources we accept, in order of preference. slam_toolbox's
        # /pose is the authoritative map-frame pose during mapping. Subscribe
        # to all in case any of them is the live one in the current mode.
        self.create_subscription(
            PoseWithCovarianceStamped, "/pose", self._pose_cov_cb, 10
        )
        self.create_subscription(Odometry, "/odom", self._odom_cb, 10)
        self.create_subscription(Odometry, "/mapping_pose", self._odom_cb, 10)

        # /map is typically published with TRANSIENT_LOCAL durability.
        map_qos = QoSProfile(
            depth=1,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
        )
        self.create_subscription(OccupancyGrid, "/map", self._map_cb, map_qos)
        self.create_subscription(BatteryState, "/battery_state", self._battery_cb, 10)
        self.create_subscription(LaserScan, "/scan", self._scan_cb, 10)
        self.create_subscription(
            Image,
            "/mars/main_camera/left/image_raw",
            self._image_cb,
            10,
        )
        if depth_topic:
            self.create_subscription(Image, depth_topic, self._depth_cb, 10)
        if camera_info_topic:
            self.create_subscription(CameraInfo, camera_info_topic, self._camera_info_cb, 10)

        msg = (
            "map_stream_node subscribed to /pose, /odom, /mapping_pose, /map, "
            "/battery_state, /scan, /mars/main_camera/left/image_raw"
        )
        if depth_topic:
            msg += f", {depth_topic}"
        if camera_info_topic:
            msg += f", {camera_info_topic}"
        self.get_logger().info(msg)

    def _store_pose(self, x: float, y: float, theta: float, source: str) -> None:
        with self._lock:
            first = self._pose is None
            self._pose = (x, y, theta)
        if first:
            self.get_logger().info(
                f"first pose from {source}: x={x:.3f} y={y:.3f} theta={theta:.3f}"
            )

    def _pose_cov_cb(self, msg: PoseWithCovarianceStamped) -> None:
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self._store_pose(p.x, p.y, _yaw_from_quat(q.x, q.y, q.z, q.w), "/pose")

    def _odom_cb(self, msg: Odometry) -> None:
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self._store_pose(
            p.x, p.y, _yaw_from_quat(q.x, q.y, q.z, q.w), "odom-like"
        )

    def _map_cb(self, msg: OccupancyGrid) -> None:
        with self._lock:
            self._last_map = msg

    def _battery_cb(self, msg: BatteryState) -> None:
        if msg.percentage < 0.0:
            return
        pct = float(msg.percentage)
        if pct <= 1.0:
            pct *= 100.0
        with self._lock:
            self._battery_pct = pct

    def _scan_cb(self, msg: LaserScan) -> None:
        with self._lock:
            self._last_scan = msg

    def _image_cb(self, msg: Image) -> None:
        """Drop raw frame into the encode queue — never blocks the spin thread."""
        try:
            import numpy as np
            frame = np.frombuffer(bytes(msg.data), dtype=np.uint8).reshape(
                msg.height, msg.width, -1
            )
        except Exception as exc:
            self.get_logger().warn(f"image reshape failed: {exc}")
            return
        try:
            self._encode_queue.put_nowait(frame)
        except Exception:
            pass  # queue full — drop stale frame, keep latest

    def _encode_loop(self) -> None:
        """Background thread: compress frames from the encode queue to JPEG."""
        import cv2
        while True:
            frame = self._encode_queue.get()
            try:
                ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    with self._lock:
                        self._last_image_bytes = buf.tobytes()
            except Exception:
                pass

    def _depth_cb(self, msg: Image) -> None:
        try:
            depth_m = decode_depth_image(
                bytes(msg.data),
                msg.width,
                msg.height,
                msg.encoding,
                msg.step,
                depth_scale=self._depth_scale,
            )
            with self._lock:
                self._last_depth_m = depth_m
        except Exception as exc:
            self.get_logger().warn(f"depth decode failed: {exc}")

    def _camera_info_cb(self, msg: CameraInfo) -> None:
        info = camera_info_to_dict(msg)
        if info is not None:
            with self._lock:
                self._camera_info = info

    def get_image_b64(self) -> str | None:
        """Return the latest camera frame as base64, or None if no frame yet."""
        import base64
        with self._lock:
            if self._last_image_bytes is None:
                return None
            return base64.b64encode(self._last_image_bytes).decode()

    def set_vlm_result(self, result: dict) -> None:
        with self._lock:
            self._vlm_result = result
            self._vlm_result_ts = time.time()

    def get_vlm_result(self) -> dict:
        with self._lock:
            return dict(self._vlm_result)

    # -- Autonomy --------------------------------------------------------

    def set_autonomy(self, enabled: bool) -> None:
        if enabled and not AUTONOMY_SWITCHING_ENABLED:
            self.get_logger().info("autonomy enable ignored: autonomous switching disabled")
            return
        with self._lock:
            self._autonomy_enabled = enabled
        self.get_logger().info(f"autonomy {'ENABLED' if enabled else 'DISABLED'}")

    @property
    def autonomy_enabled(self) -> bool:
        with self._lock:
            return self._autonomy_enabled

    def set_pending_command(self, cmd) -> None:
        with self._lock:
            self._pending_cmd = {"kind": cmd.kind, "reason": cmd.reason}

    def get_planner_state(self) -> dict:
        with self._lock:
            return {
                "enabled": self._autonomy_enabled,
                "cmd": dict(self._pending_cmd),
            }

    def set_planner_phase(self, phase: str) -> None:
        with self._lock:
            self._planner_phase = phase

    def get_planner_phase(self) -> str:
        with self._lock:
            return self._planner_phase

    def set_alert(self, msg: str) -> None:
        with self._lock:
            self._alert = msg

    def get_and_clear_alert(self) -> str | None:
        with self._lock:
            msg, self._alert = self._alert, None
            return msg

    def get_depth_at_bbox(self, bbox: list) -> float | None:
        """Return median depth in metres at the bounding box centre.

        bbox uses the VLM coordinate system: [y_min, x_min, y_max, x_max] 0–1000.
        Returns None if depth data is unavailable or the region is invalid.
        """
        try:
            import numpy as np

            with self._lock:
                depth_m = self._last_depth_m
            if depth_m is None or depth_m.ndim != 2:
                return None
            h, w = depth_m.shape
            y1 = int(bbox[0] * h / 1000)
            x1 = int(bbox[1] * w / 1000)
            y2 = int(bbox[2] * h / 1000)
            x2 = int(bbox[3] * w / 1000)
            y1, y2 = max(0, y1), min(h, y2)
            x1, x2 = max(0, x1), min(w, x2)
            if y2 <= y1 or x2 <= x1:
                return None
            region = depth_m[y1:y2, x1:x2]
            valid = region[(region > 0.1) & (region < 10.0)]
            return float(np.median(valid)) if valid.size > 0 else None
        except Exception:
            return None

    def get_min_forward_range(self, arc_half_rad: float = math.pi / 6) -> float | None:
        """Return the minimum LiDAR range in the forward arc (±arc_half_rad).

        Returns None if no scan is available. The forward direction is 0 rad
        (straight ahead in the laser frame).
        """
        with self._lock:
            scan = self._last_scan
        if scan is None:
            return None
        try:
            idx_center = int(round((0.0 - scan.angle_min) / scan.angle_increment))
            idx_half = max(1, int(arc_half_rad / scan.angle_increment))
            idx_start = max(0, idx_center - idx_half)
            idx_end = min(len(scan.ranges), idx_center + idx_half)
            forward = [
                r for r in scan.ranges[idx_start:idx_end]
                if scan.range_min < r < scan.range_max
            ]
        except Exception:
            return None
        return min(forward) if forward else None

    def publish_defusal_action(self, action: str) -> None:
        from std_msgs.msg import String  # noqa: PLC0415
        msg = String()
        msg.data = action
        self._defusal_action_pub.publish(msg)
        self.get_logger().info(f"defusal action published: {action}")

    def publish_twist(self, linear_x: float, angular_z: float) -> None:
        from geometry_msgs.msg import Twist  # noqa: PLC0415

        twist = Twist()
        twist.linear.x = float(linear_x)
        twist.angular.z = float(angular_z)
        self._cmd_vel_pub.publish(twist)

    def handle_operator_command(self, text: str) -> tuple[str, bool]:
        command = " ".join(text.lower().replace("_", " ").split())
        if not command:
            return "No command entered", True

        if command in {"autonomy on", "enable autonomy", "auto on"}:
            if not AUTONOMY_SWITCHING_ENABLED:
                return "Autonomous switching is disabled; use manual commands", True
            self.set_autonomy(True)
            return "Autonomy enabled", False
        if command in {"autonomy off", "disable autonomy", "auto off"}:
            self.set_autonomy(False)
            return "Autonomy disabled", False
        if command in {"stop", "halt", "emergency stop", "e stop", "estop"}:
            self.set_autonomy(False)
            self.stop_manual_motion()
            return "Stopped motion and disabled autonomy", False

        defusal_actions = {
            "abort": "ABORT",
            "cut red": "CUT_RED",
            "red": "CUT_RED",
            "cut blue": "CUT_BLUE",
            "blue": "CUT_BLUE",
            "cut green": "CUT_GREEN",
            "green": "CUT_GREEN",
            "flip switch": "FLIP_SWITCH",
            "switch": "FLIP_SWITCH",
        }
        action = defusal_actions.get(command)
        if action:
            self.publish_defusal_action(action)
            return f"Published defusal action {action}", False

        motion = self._parse_manual_motion(command)
        if motion is not None:
            label, linear_x, angular_z, duration = motion
            self.set_autonomy(False)
            self.start_manual_motion(linear_x, angular_z, duration)
            return f"Manual motion: {label} for {duration:.1f}s; autonomy disabled", False

        return (
            "Unknown command. Try: forward, back, left, right, stop, "
            "autonomy on/off, cut red/blue/green, flip switch, abort",
            True,
        )

    def _parse_manual_motion(self, command: str) -> tuple[str, float, float, float] | None:
        tokens = command.split()
        duration = 0.7
        for token in tokens:
            try:
                duration = max(0.1, min(float(token), 1.5))
                break
            except ValueError:
                continue

        if any(word in tokens for word in ("forward", "ahead")):
            return "forward", 0.08, 0.0, duration
        if any(word in tokens for word in ("back", "backward", "reverse")):
            return "back", -0.06, 0.0, duration
        if "left" in tokens:
            return "left", 0.0, 0.35, duration
        if "right" in tokens:
            return "right", 0.0, -0.35, duration
        return None

    def _next_manual_motion_token(self) -> int:
        with self._lock:
            self._manual_motion_token += 1
            return self._manual_motion_token

    def _manual_motion_is_current(self, token: int) -> bool:
        with self._lock:
            return self._manual_motion_token == token

    def start_manual_motion(self, linear_x: float, angular_z: float, duration: float) -> None:
        token = self._next_manual_motion_token()
        thread = threading.Thread(
            target=self._run_manual_motion,
            args=(token, linear_x, angular_z, duration),
            daemon=True,
        )
        thread.start()

    def stop_manual_motion(self) -> None:
        self._next_manual_motion_token()
        from geometry_msgs.msg import Twist  # noqa: PLC0415
        self._cmd_vel_pub.publish(Twist())

    def _run_manual_motion(
        self,
        token: int,
        linear_x: float,
        angular_z: float,
        duration: float,
    ) -> None:
        from geometry_msgs.msg import Twist  # noqa: PLC0415

        twist = Twist()
        twist.linear.x = linear_x
        twist.angular.z = angular_z
        is_forward = linear_x > 0
        deadline = time.time() + duration
        last_lidar_check = 0.0
        try:
            while time.time() < deadline and self._manual_motion_is_current(token):
                now = time.time()
                if is_forward and (now - last_lidar_check) >= _LIDAR_CHECK_INTERVAL:
                    min_range = self.get_min_forward_range()
                    if min_range is not None and min_range < _OBSTACLE_CLEARANCE_M:
                        self.get_logger().warn(
                            f"Obstacle {min_range:.2f}m ahead — stopping manual motion"
                        )
                        break
                    last_lidar_check = now
                self._cmd_vel_pub.publish(twist)
                time.sleep(0.05)
        finally:
            self._cmd_vel_pub.publish(Twist())

    def get_semantic_markers(self, now: float) -> list[dict]:
        with self._lock:
            vlm_ts = self._vlm_result_ts
            if not vlm_ts or (now - vlm_ts) > SEMANTIC_MARKER_TTL:
                return []
            # Cache hit: VLM result hasn't changed since last projection.
            if vlm_ts == self._cached_markers_ts:
                return list(self._cached_markers)
            annotations = self._vlm_result.get("annotations", [])
            depth_m = self._last_depth_m
            pose = self._pose
            camera_info = dict(self._camera_info) if self._camera_info else None

        markers = markers_from_annotations(
            annotations,
            depth_m,
            pose,
            camera_info=camera_info,
            now=vlm_ts,
        )
        with self._lock:
            self._cached_markers = markers
            self._cached_markers_ts = vlm_ts
        return list(markers)

    def snapshot(
        self,
    ) -> tuple[
        tuple[float, float, float] | None,
        OccupancyGrid | None,
        LaserScan | None,
        float | None,
    ]:
        with self._lock:
            return self._pose, self._last_map, self._last_scan, self._battery_pct


def build_robot_payload(
    pose: tuple[float, float, float], battery_pct: float | None
) -> dict:
    x, y, theta = pose
    out: dict = {"x": x, "y": y, "theta": theta}
    if battery_pct is not None:
        out["battery"] = int(round(battery_pct))
    else:
        out["battery"] = 100
    return out


def build_scan_payload(scan: LaserScan) -> dict:
    return {
        "scan": {
            "angle_min": float(scan.angle_min),
            "angle_max": float(scan.angle_max),
            "angle_increment": float(scan.angle_increment),
            "range_min": float(scan.range_min),
            "range_max": float(scan.range_max),
            "ranges": [float(r) for r in scan.ranges],
        }
    }


def build_map_payload(occ: OccupancyGrid) -> dict:
    info = occ.info
    return {
        "map": {
            "width": info.width,
            "height": info.height,
            "resolution": info.resolution,
            "origin": {
                "x": info.origin.position.x,
                "y": info.origin.position.y,
            },
            "data": list(occ.data),
        }
    }


def _serve_static(request_path: str):
    """Map an HTTP request path to (status, content-type, body) from DASHBOARD_DIR.

    Returns (404, "text/plain", b"not found") if the file doesn't exist or
    escapes the dashboard dir. Used as the non-WebSocket fallback for the
    combined HTTP+WS server.
    """
    rel = request_path.lstrip("/") or "index.html"
    target = (DASHBOARD_DIR / rel).resolve()
    try:
        target.relative_to(DASHBOARD_DIR)
    except ValueError:
        return 403, "text/plain", b"forbidden"
    if not target.is_file():
        return 404, "text/plain", b"not found"
    ctype, _ = mimetypes.guess_type(str(target))
    return 200, ctype or "application/octet-stream", target.read_bytes()


def _init_intruder_alert():
    """Try to set up ElevenLabs TTS + person detection for intruder alerts.

    Returns (PersonDetector, ElevenLabsTTS) or (None, None) if deps are
    missing or ELEVENLABS_API_KEY is not set.
    """
    import os
    try:
        from intruder_alert.person_detector import PersonDetector
        from intruder_alert.elevenlabs_tts import ElevenLabsTTS
    except ImportError:
        print("[ALERT] intruder_alert module not found — alerts disabled.")
        return None, None

    if not os.environ.get("ELEVENLABS_API_KEY"):
        print("[ALERT] ELEVENLABS_API_KEY not set — intruder alerts disabled.")
        return None, None

    detector = PersonDetector(cooldown_seconds=15.0)
    tts = ElevenLabsTTS()

    # Pre-cache the default warning so the first alert plays instantly.
    try:
        tts.synthesize(
            "Attention. This is an emergency. A potential explosive device "
            "has been detected in this area. For your safety, evacuate the "
            "building immediately. Move away from the area calmly and quickly. "
            "Do not touch any suspicious objects. Emergency services have been "
            "contacted. Please proceed to the nearest exit now."
        )
        print("[ALERT] Evacuation alert system armed — audio pre-cached.")
    except Exception as exc:
        print(f"[ALERT] Failed to pre-cache audio: {exc}")

    return detector, tts


def _handle_intruder_alert(
    vlm_result: dict,
    detector,
    tts,
) -> None:
    """Check VLM result for people and play an audio warning if found."""
    people = detector.extract_people(vlm_result)
    if not people:
        return

    if not detector.should_alert():
        return

    closest = max(people, key=lambda p: p.bbox_area)
    print(
        f"[ALERT] Person detected: {closest.label} "
        f"(size={closest.size_proxy:.3f}) — issuing evacuation warning"
    )
    detector.mark_alerted()

    tts.speak_async(
        "Attention. This is an emergency. A potential explosive device "
        "has been detected in this area. For your safety, evacuate the "
        "building immediately. Move away from the area calmly and quickly. "
        "Do not touch any suspicious objects. Emergency services have been "
        "contacted. Please proceed to the nearest exit now."
    )


def run_vlm_thread(node: MapStreamNode) -> None:
    """Background thread: grab camera frames and call Gemini every VLM_INTERVAL seconds.

    Results are stored on the node and merged into the next broadcaster payload.
    Requires GEMINI_API_KEY to be set in the environment.

    When ELEVENLABS_API_KEY is also set, automatically plays an audio
    warning through the robot speakers whenever a person is detected.
    """
    import os
    if not os.environ.get("GEMINI_API_KEY"):
        print("[VLM] GEMINI_API_KEY not set — VLM analysis disabled.")
        return

    try:
        from vlm import VLMSession
        from vlm.analyze import analyze_frame
    except ImportError:
        print("[VLM] vlm module not found — run from repo root or add to PYTHONPATH.")
        return

    session = VLMSession()
    detector, tts = _init_intruder_alert()
    print("[VLM] VLM thread started.")

    while True:
        time.sleep(VLM_INTERVAL)
        image_b64 = node.get_image_b64()
        if image_b64 is None:
            continue
        try:
            planner_phase = node.get_planner_phase()
            if planner_phase == "approach":
                # Bypass VLMSession: call defusal prompt directly so the
                # defusal/wires keys are NOT stripped before reaching the dashboard.
                result = analyze_frame(image_b64, phase="defusal")
            else:
                # "recon" or "done": use session for cumulative rooms tracking.
                result = session.update(image_b64)
            node.set_vlm_result(result)

            if detector and tts:
                _handle_intruder_alert(result, detector, tts)
        except Exception as exc:
            print(f"[VLM] analysis error: {exc}")


async def serve(node: MapStreamNode, host: str, port: int) -> None:
    import websockets
    from websockets.asyncio.server import Response
    from websockets.datastructures import Headers
    try:
        from slam.command_executor import CommandExecutor
    except ModuleNotFoundError as exc:  # pragma: no cover - script execution fallback.
        if exc.name != "slam":
            raise
        from command_executor import CommandExecutor

    clients: set = set()

    async def broadcast_status(status: dict) -> None:
        payload = {"type": "status", **status}
        if not clients:
            return
        encoded = json.dumps(payload)
        stale = []
        for client in list(clients):
            try:
                await client.send(encoded)
            except Exception:
                stale.append(client)
        for client in stale:
            clients.discard(client)

    command_executor = CommandExecutor(node, broadcast_status)
    await command_executor.start()

    def process_request(connection, request):
        """Return an HTTP Response for non-WebSocket requests (static files).

        If the client sent an Upgrade: websocket header, returning None lets
        the handshake proceed. Otherwise, synthesize an HTTP response from
        the dashboard/ directory.
        """
        if request.headers.get("Upgrade", "").lower() == "websocket":
            return None  # let the WS handshake proceed
        status, ctype, body = _serve_static(request.path)
        return Response(
            status_code=status,
            reason_phrase={200: "OK", 403: "Forbidden", 404: "Not Found"}.get(status, "OK"),
            headers=Headers(
                [
                    ("Content-Type", ctype),
                    ("Content-Length", str(len(body))),
                    ("Cache-Control", "no-store"),
                    ("Connection", "close"),
                ]
            ),
            body=body,
        )

    async def handler(ws):
        clients.add(ws)
        node.get_logger().info(f"client connected ({len(clients)} total)")
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                if msg.get("cmd") == "set_autonomy":
                    enabled = bool(msg.get("enabled", False))
                    node.set_autonomy(enabled)
                    if enabled and not AUTONOMY_SWITCHING_ENABLED:
                        await ws.send(json.dumps({
                            "type": "status",
                            "phase": "error",
                            "text": "Autonomous switching is disabled; use manual commands",
                        }))
                elif msg.get("cmd") == "defusal_action":
                    action = str(msg.get("action", "")).strip()
                    if action:
                        node.publish_defusal_action(action)
                elif msg.get("cmd") == "operator_command":
                    text = str(msg.get("text", "")).strip()
                    status, is_error = node.handle_operator_command(text)
                    await ws.send(json.dumps({
                        "type": "status",
                        "phase": "error" if is_error else "done",
                        "text": status,
                    }))
                elif msg.get("type") == "action":
                    text = str(msg.get("text", "")).strip()
                    if not text:
                        await ws.send(json.dumps({
                            "type": "status",
                            "phase": "error",
                            "text": "empty command",
                        }))
                        continue

                    command = " ".join(text.lower().replace("_", " ").split())
                    if command in {"stop", "halt", "emergency stop", "e stop", "estop"}:
                        node.set_autonomy(False)
                        node.stop_manual_motion()
                        await command_executor.stop()
                        continue

                    status, is_error = node.handle_operator_command(text)
                    if not is_error:
                        phase = (
                            "executing"
                            if status.startswith("Manual motion:")
                            else "done"
                        )
                        await broadcast_status({"phase": phase, "text": status})
                        continue
                    if not status.startswith("Unknown command"):
                        await broadcast_status({"phase": "error", "text": status})
                        continue

                    node.set_autonomy(False)
                    node.stop_manual_motion()
                    await command_executor.submit(text)
                elif msg.get("type") == "stop":
                    node.set_autonomy(False)
                    node.stop_manual_motion()
                    await command_executor.stop()
        finally:
            clients.discard(ws)
            node.get_logger().info(f"client disconnected ({len(clients)} total)")

    async def broadcaster() -> None:
        pose_interval = 1.0 / POSE_HZ
        map_interval = 1.0 / MAP_HZ
        scan_interval = 1.0 / SCAN_HZ
        last_map_push = 0.0
        last_scan_push = 0.0
        last_vlm_push_ts = 0.0
        while True:
            pose, occ, scan, bat = node.snapshot()
            payload: dict = {
                "timestamp": time.time(),
                "mission_phase": "recon",
            }
            if pose is not None:
                payload["robot"] = build_robot_payload(pose, bat)
            now = time.time()
            if occ is not None and (now - last_map_push) >= map_interval:
                payload["slam"] = build_map_payload(occ)
                last_map_push = now
            elif (
                occ is None
                and scan is not None
                and pose is not None
                and (now - last_scan_push) >= scan_interval
            ):
                payload["slam"] = build_scan_payload(scan)
                last_scan_push = now

            # Merge latest VLM result only when Gemini has produced a new frame.
            vlm = node.get_vlm_result()
            with node._lock:
                vlm_ts = node._vlm_result_ts
            if vlm and vlm_ts > last_vlm_push_ts:
                payload.update(vlm)
                last_vlm_push_ts = vlm_ts
            payload["semantic_markers"] = node.get_semantic_markers(now)
            payload["autonomy"] = node.get_planner_state()
            # Only consume the alert when there are clients — if no browser is
            # connected the alert would be cleared and permanently lost.
            alert = node.get_and_clear_alert() if clients else None
            if alert is not None:
                payload["alert"] = alert

            if clients:
                msg = json.dumps(payload)
                stale = []
                for c in list(clients):
                    try:
                        await c.send(msg)
                    except Exception:
                        stale.append(c)
                for c in stale:
                    clients.discard(c)

            await asyncio.sleep(pose_interval)

    async with websockets.serve(handler, host, port, process_request=process_request):
        node.get_logger().info(
            f"HTTP+WS server listening on http://{host}:{port}/ (ws at /ws)"
        )
        await broadcaster()


_OBSTACLE_CLEARANCE_M = 0.5   # minimum forward range before blocking motion
_LIDAR_CHECK_INTERVAL = 0.5   # re-check LiDAR every N seconds during a forward command


def _execute_command(node: MapStreamNode, cmd: "RobotCommand") -> None:
    """Translate a RobotCommand into /cmd_vel publishes.

    Blocks for the duration of the command so the planner loop naturally
    waits before requesting the next one.  Aborts early if autonomy is
    disabled mid-command or a LiDAR obstacle is detected during forward motion.
    """
    from geometry_msgs.msg import Twist  # noqa: PLC0415

    OMEGA = 0.3  # rad/s used for rotate commands

    def _publish_for(twist: "Twist", duration: float) -> None:
        is_forward = twist.linear.x > 0
        deadline = time.time() + duration
        last_lidar_check = 0.0
        while time.time() < deadline:
            if not node.autonomy_enabled:
                break
            # LiDAR safety: re-check the forward arc periodically.
            now = time.time()
            if is_forward and (now - last_lidar_check) >= _LIDAR_CHECK_INTERVAL:
                min_range = node.get_min_forward_range()
                if min_range is not None and min_range < _OBSTACLE_CLEARANCE_M:
                    node.get_logger().warn(
                        f"Obstacle {min_range:.2f}m ahead — stopping forward motion"
                    )
                    break
                last_lidar_check = now
            node._cmd_vel_pub.publish(twist)
            time.sleep(0.05)
        # Always send a zero-velocity stop after the command.
        node._cmd_vel_pub.publish(Twist())

    if cmd.kind == "rotate":
        t = Twist()
        t.angular.z = math.copysign(OMEGA, cmd.angle)
        _publish_for(t, abs(cmd.angle) / OMEGA)

    elif cmd.kind == "cmd_vel":
        t = Twist()
        t.linear.x = cmd.linear_x
        t.angular.z = cmd.angular_z
        _publish_for(t, cmd.duration)

    elif cmd.kind == "wait":
        deadline = time.time() + cmd.duration
        while time.time() < deadline and node.autonomy_enabled:
            time.sleep(0.1)


def run_planner_thread(node: MapStreamNode) -> None:
    """Background thread: call the Planner every cycle and optionally execute.

    When autonomy is disabled the thread still runs — it keeps the planner
    state live and populates ``pending_cmd`` so the dashboard can show the
    operator what the robot *would* do next.
    """
    try:
        from vlm import Planner
    except ImportError:
        print("[Planner] vlm module not found — planner thread disabled.")
        return

    planner = Planner()
    print("[Planner] Planner thread started.")

    while True:
        vlm_result = node.get_vlm_result()

        if not vlm_result:
            time.sleep(1.0)
            continue

        # If Gemini has been failing, _vlm_result_ts falls behind. After two
        # missed VLM cycles (2 × VLM_INTERVAL), strip threat signals so the
        # planner doesn't keep chasing a threat from a stale frame.
        with node._lock:
            result_age = time.time() - node._vlm_result_ts
        if result_age > VLM_INTERVAL * 2:
            vlm_result = {**vlm_result,
                          "threat_detected": False,
                          "annotations": [],
                          "defusal": {}}

        if node.autonomy_enabled:
            # Augment VLM result with live depth for the priority threat target,
            # so the planner can use real distance instead of bbox size proxy.
            target = planner._find_priority_target(vlm_result)
            if target:
                try:
                    depth = node.get_depth_at_bbox(target["bbox"])
                except Exception:
                    depth = None
                if depth is not None:
                    vlm_result = {**vlm_result, "_threat_depth_m": depth}

            # Mutate planner state and execute the command.
            cmd = planner.next_command(vlm_result)
            node.set_pending_command(cmd)
            node.set_planner_phase(planner.phase)

            if cmd.kind == "done":
                node.set_autonomy(False)
                node.set_alert(cmd.reason)
                node.set_planner_phase("done")  # freeze VLM on defusal prompt until reset
                planner.reset()
                time.sleep(1.0)
            else:
                _execute_command(node, cmd)
        else:
            # Autonomy OFF: preview without mutating — counter stays frozen.
            cmd = planner.preview_command(vlm_result)
            node.set_pending_command(cmd)
            # Guard: don't overwrite "done" — it was set by the done-handler and
            # must survive until the VLM thread (3s cadence) reads it. Once the
            # VLM thread has switched to defusal prompts it will no longer matter.
            if node.get_planner_phase() != "done":
                node.set_planner_phase(planner.phase)
            time.sleep(0.2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--depth-topic", default=DEFAULT_DEPTH_TOPIC)
    ap.add_argument("--camera-info-topic", default=DEFAULT_CAMERA_INFO_TOPIC)
    ap.add_argument("--depth-scale", type=float, default=0.001)
    args = ap.parse_args()

    rclpy.init()
    node = MapStreamNode(
        depth_topic=args.depth_topic,
        camera_info_topic=args.camera_info_topic,
        depth_scale=args.depth_scale,
    )

    # rclpy.spin in a dedicated thread so asyncio owns the main thread.
    spin_thread = threading.Thread(
        target=lambda: rclpy.spin(node), daemon=True
    )
    spin_thread.start()

    # VLM analysis in its own thread — runs every VLM_INTERVAL seconds.
    vlm_thread = threading.Thread(
        target=run_vlm_thread, args=(node,), daemon=True
    )
    vlm_thread.start()

    # Planner thread — reads VLM results, executes commands when autonomy is on.
    planner_thread = threading.Thread(
        target=run_planner_thread, args=(node,), daemon=True
    )
    planner_thread.start()

    try:
        asyncio.run(serve(node, args.host, args.port))
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
