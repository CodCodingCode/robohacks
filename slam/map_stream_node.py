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
import socket
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
from nav_msgs.srv import GetMap
from sensor_msgs.msg import BatteryState, CameraInfo, Image, LaserScan
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from lifecycle_msgs.srv import ChangeState, GetState
from lifecycle_msgs.msg import Transition
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
# LiDAR fallback when /map is empty.
SCAN_HZ = 1.0
# VLM analysis cadence — Gemini rate limit is 1s minimum.
VLM_INTERVAL = 2.0
SEMANTIC_MARKER_TTL = 8.0
AUTONOMY_SWITCHING_ENABLED = True

# LD2450 radar UDP ingest
RADAR_UDP_PORT = 8766
RADAR_TARGET_TTL = 1.5  # seconds before a target is considered stale

# Sensor mount offsets in metres, relative to robot center (matching geometry.json).
# x = lateral (negative = left), y = forward.
SENSOR_MOUNTS: dict[int, tuple[float, float]] = {
    0: (-0.120, 0.0),   # S0: 120mm left
    1: ( 0.000, 0.0),   # S1: center
    2: ( 0.120, 0.0),   # S2: 120mm right
}


class RadarListener:
    """Reads LD2450 detections from ESP32 nodes via USB serial, and optionally
    from UDP (for mock_radar_sender.py testing).

    Serial packets from the ESPs arrive as JSON lines:
        {"msg": "detections", "node_id": "A",
         "detections": [{"sensor_id": "S0", "x_mm": 450, "y_mm": 2000,
                         "speed_cms": 0, "active": true, ...}, ...]}

    UDP mock packets (mock_radar_sender.py):
        {"sensor_id": 1, "ts": <float>,
         "targets": [{"x_mm": int, "y_mm": int, "v_cms": int}]}
    """

    _SID_TO_IDX: dict[str, int] = {
        "S0": 0, "S1": 1, "S2": 2,
        "0": 0,  "1": 1,  "2": 2,
    }

    @staticmethod
    def _parse_sensor_idx(raw_sid) -> int | None:
        """Map sensor_id to internal index, handling 'S0' strings, bare '0' strings, and ints."""
        if isinstance(raw_sid, int):
            return raw_sid if 0 <= raw_sid <= 2 else None
        s = str(raw_sid).strip().upper()
        return RadarListener._SID_TO_IDX.get(s)

    def __init__(
        self,
        serial_ports: dict[str, str] | None = None,
        udp_port: int = RADAR_UDP_PORT,
    ) -> None:
        self._lock = threading.Lock()
        self._targets: dict[int, list[tuple[float, float, float, float]]] = {}

        self._serial_rx = None
        self._serial_det_count = 0
        if serial_ports:
            print(f"[RADAR] Serial ports config: {serial_ports}")
            try:
                from transport_serial import SerialNodeReceiver
            except ImportError:
                from slam.transport_serial import SerialNodeReceiver
            self._serial_rx = SerialNodeReceiver(serial_ports)
            self._serial_rx.start()
            self._serial_thread = threading.Thread(
                target=self._serial_poll_loop, daemon=True
            )
            self._serial_thread.start()
            print("[RADAR] Serial poll thread started")
        else:
            print("[RADAR] No serial ports configured — serial radar disabled")

        self._udp_thread = threading.Thread(
            target=self._udp_loop, args=(udp_port,), daemon=True
        )
        self._udp_thread.start()
        print(f"[RADAR] UDP listener started on port {udp_port}")

    def _serial_poll_loop(self) -> None:
        while True:
            pkt = self._serial_rx.pop()
            if pkt is None:
                time.sleep(0.01)
                continue
            data = pkt.data
            if data.get("msg") != "detections":
                if self._serial_det_count == 0:
                    print(f"[RADAR] Serial got non-detection msg: {data.get('msg', '?')} from node {pkt.node_id}")
                continue
            now = time.time()
            active_count = 0
            new_targets: dict[int, list[tuple[float, float, float, float]]] = {}
            for det in data.get("detections", []):
                if not det.get("active", False):
                    continue
                idx = self._parse_sensor_idx(det.get("sensor_id", ""))
                if idx is None:
                    continue
                x_m = int(det.get("x_mm", 0)) / 1000.0
                y_m = int(det.get("y_mm", 0)) / 1000.0
                speed = int(det.get("speed_cms", 0)) / 100.0
                new_targets.setdefault(idx, []).append(
                    (x_m, y_m, speed, now)
                )
                active_count += 1
            with self._lock:
                for idx, targets in new_targets.items():
                    self._targets[idx] = targets
            self._serial_det_count += 1
            if self._serial_det_count <= 3 or self._serial_det_count % 100 == 0:
                print(f"[RADAR] Serial frame #{self._serial_det_count} from {pkt.node_id}: {active_count} active targets")

    def _udp_loop(self, port: int) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        while True:
            try:
                data, _ = sock.recvfrom(4096)
                msg = json.loads(data)
                sid = int(msg.get("sensor_id", 0))
                now = time.time()
                targets = []
                for t in msg.get("targets", []):
                    x_m = t["x_mm"] / 1000.0
                    y_m = t["y_mm"] / 1000.0
                    speed = t.get("v_cms", 0) / 100.0
                    targets.append((x_m, y_m, speed, now))
                with self._lock:
                    self._targets[sid] = targets
            except Exception:
                pass

    def get_world_targets(
        self,
        robot_pose: tuple[float, float, float] | None,
    ) -> list[dict]:
        now = time.time()
        rx, ry, theta = robot_pose if robot_pose else (0.0, 0.0, 0.0)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        result: list[dict] = []
        tid = 0
        with self._lock:
            for sid, targets in self._targets.items():
                mx, my = SENSOR_MOUNTS.get(sid, (0.0, 0.0))
                fresh = [t for t in targets if (now - t[3]) < RADAR_TARGET_TTL]
                self._targets[sid] = fresh
                for lx, ly, speed, _ts in fresh:
                    rel_x = mx + lx
                    rel_y = my + ly
                    wx = rx + rel_x * cos_t - rel_y * sin_t
                    wy = ry + rel_x * sin_t + rel_y * cos_t
                    result.append({
                        "id": tid,
                        "x": round(wx, 3),
                        "y": round(wy, 3),
                        "speed": round(speed, 2),
                        "confidence": 0.7,
                    })
                    tid += 1
        return result


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
        self._last_map_stamp: float = 0.0  # ROS header stamp (seconds)
        self._have_live_slam: bool = False  # True once dynamic_map responds
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
        # Latest approach loop telemetry from recon_movement skill.
        self._approach_state: dict = {}
        self._approach_state_ts: float = 0.0
        # Semantic marker cache — recomputed only when _vlm_result_ts changes.
        self._cached_markers: list = []
        self._cached_markers_ts: float = 0.0
        # Persistent object store — accumulates VLM detections for the session.
        # Keyed by stable_marker_id(). Lives in memory, cleared on restart.
        self._persistent_markers: dict[str, dict] = {}
        # One-time diagnostic flags so we only log missing topics once.
        self._warned_no_map: bool = False
        self._warned_no_depth: bool = False
        self._warned_no_camera_info: bool = False
        self._start_time: float = time.time()
        # Autonomy: operator-controlled toggle for planner execution.
        self._autonomy_enabled: bool = False
        self._pending_cmd: dict = {}  # {"kind": str, "reason": str}
        # Planner phase — synced by run_planner_thread so run_vlm_thread can
        # switch Gemini prompts without direct access to the Planner object.
        self._planner_phase: str = "recon"
        # One-shot alert: set when autonomy auto-disables on "done", cleared on read.
        self._alert: str | None = None
        self._manual_motion_token: int = 0
        self._tts = None  # ElevenLabsTTS instance, set by run_vlm_thread
        self._mission_running: bool = False
        self._mission_broadcast_fn = None  # set by serve() for mission_update msgs

        # /cmd_vel publisher — used by the planner thread when autonomy is on.
        from geometry_msgs.msg import Twist  # noqa: PLC0415
        from std_msgs.msg import String  # noqa: PLC0415
        self._cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        # /defusal_action publisher — operator wire-cut / switch commands.
        self._defusal_action_pub = self.create_publisher(String, "/defusal_action", 10)

        # Shared VLM annotations — skills read pre-computed results from here
        # instead of making their own blocking Gemini calls.
        from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy  # noqa: PLC0415
        _latched_qos = QoSProfile(
            depth=1,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
        )
        self._vlm_annotations_pub = self.create_publisher(
            String, "/recon/vlm_annotations", _latched_qos
        )

        # Brain agent chat bridge — dashboard commands → PEAS cloud agent.
        self._chat_in_pub = self.create_publisher(String, "/brain/chat_in", 10)
        self._set_directive_pub = self.create_publisher(String, "/brain/set_directive", 10)
        self._chat_out_queue = None   # asyncio.Queue, set by set_chat_loop()
        self._chat_out_loop = None    # asyncio event loop, set by set_chat_loop()
        self._active_directive: str | None = None
        self._skills_loaded: bool = False  # True once available_skills contains our skill
        self.create_subscription(String, "/brain/chat_out", self._chat_out_cb, 10)
        self.create_subscription(String, "/brain/skill_status_update", self._skill_status_cb, 10)
        # Watch available_skills — re-register recon_agent once our skill appears.
        try:
            from brain_messages.msg import AvailableSkills  # noqa: PLC0415
            _avail_qos = QoSProfile(
                depth=1,
                durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                reliability=QoSReliabilityPolicy.RELIABLE,
            )
            self.create_subscription(
                AvailableSkills, "/brain/available_skills",
                self._available_skills_cb, _avail_qos,
            )
        except Exception:
            pass  # brain_messages not available in offline/test mode

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
        self.create_subscription(
            String, "/recon/approach_state", self._approach_state_cb, 10
        )

        # Actively poll slam_toolbox for the latest map every second.
        # The /map subscription only fires when slam_toolbox *decides* to
        # republish (usually on change). This timer ensures we always have
        # fresh map data even when the robot is stationary.
        self._dynamic_map_cli = self.create_client(
            GetMap, "/slam_toolbox/dynamic_map"
        )
        self._map_poll_timer = self.create_timer(1.0, self._poll_map)
        self._map_poll_pending = False

        # Auto-activate slam_toolbox lifecycle node so it starts mapping.
        self._slam_lifecycle_change = self.create_client(
            ChangeState, "/slam_toolbox/change_state"
        )
        self._slam_lifecycle_get = self.create_client(
            GetState, "/slam_toolbox/get_state"
        )
        self._slam_activated = False
        self._slam_activate_timer = self.create_timer(2.0, self._try_activate_slam)

        msg = (
            "map_stream_node subscribed to /pose, /odom, /mapping_pose, /map, "
            "/battery_state, /scan, /mars/main_camera/left/image_raw"
        )
        if depth_topic:
            msg += f", {depth_topic}"
        if camera_info_topic:
            msg += f", {camera_info_topic}"
        self.get_logger().info(msg)

    # ------------------------------------------------------------------
    # Brain agent bridge helpers
    # ------------------------------------------------------------------

    def set_chat_loop(self, queue, loop) -> None:
        """Wire the async queue used to hand chat_out messages to the WS loop."""
        self._chat_out_queue = queue
        self._chat_out_loop = loop

    def activate_agent(self, directive: str) -> None:
        """Switch to the given agent directive and ensure the brain is active."""
        if self._active_directive == directive:
            return
        from std_msgs.msg import String  # noqa: PLC0415
        self._set_directive_pub.publish(String(data=directive))
        self._active_directive = directive
        self.get_logger().info(f"[brain] activated directive: {directive}")

    def publish_chat_in(self, text: str) -> None:
        """Forward operator text to the active PEAS agent via /brain/chat_in."""
        from std_msgs.msg import String  # noqa: PLC0415
        import json as _json
        self._chat_in_pub.publish(String(data=_json.dumps({"text": text})))

    def _available_skills_cb(self, msg) -> None:
        """Re-register recon_agent once local/recon_movement appears in the skill list."""
        if self._skills_loaded:
            return
        skill_ids = {s.id for s in msg.skills}
        if "local/recon_movement" not in skill_ids:
            return
        self._skills_loaded = True
        # Reset cache so activate_agent() will re-publish even if already sent once.
        self._active_directive = None
        self.activate_agent("recon_agent")
        self.get_logger().info(
            "[brain] recon_movement available — re-registered recon_agent with PEAS"
        )

    def _chat_out_cb(self, msg) -> None:
        """ROS callback — push brain/chat_out to the async WS queue."""
        if not self._chat_out_queue or not self._chat_out_loop:
            return
        try:
            import json as _json
            data = _json.loads(msg.data)
        except Exception:
            return
        self._chat_out_loop.call_soon_threadsafe(self._chat_out_queue.put_nowait, data)

    def _skill_status_cb(self, msg) -> None:
        """ROS callback — push skill status updates to the async WS queue."""
        if not self._chat_out_queue or not self._chat_out_loop:
            return
        try:
            import json as _json
            data = _json.loads(msg.data)
            # Wrap as a skill_status entry so the drainer can distinguish it.
            data.setdefault("sender", "skill_status")
        except Exception:
            return
        self._chat_out_loop.call_soon_threadsafe(self._chat_out_queue.put_nowait, data)

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Persistent object store
    # ------------------------------------------------------------------

    def _merge_into_store(self, new_markers: list[dict]) -> None:
        """Merge freshly-projected markers into the persistent store (lock held by caller)."""
        MERGE_RADIUS = 1.5  # metres — same label within this radius = same object
        for m in new_markers:
            mid = m.get("id") or ""
            if not mid:
                continue
            # Check for exact ID match first (grid-cell dedup).
            existing = self._persistent_markers.get(mid)
            # If no exact match, check proximity: same label within MERGE_RADIUS.
            if existing is None:
                label = m.get("label", "")
                for eid, ev in self._persistent_markers.items():
                    if ev.get("label") != label:
                        continue
                    dx = ev["x"] - m["x"]
                    dy = ev["y"] - m["y"]
                    if (dx * dx + dy * dy) < MERGE_RADIUS * MERGE_RADIUS:
                        existing = ev
                        mid = eid  # merge into the existing entry
                        break
            if existing is None:
                self._persistent_markers[mid] = dict(m)
            else:
                # EMA position update so the dot drifts toward new observations.
                existing["x"] = 0.7 * existing["x"] + 0.3 * m["x"]
                existing["y"] = 0.7 * existing["y"] + 0.3 * m["y"]
                existing["depth_m"] = m.get("depth_m", existing.get("depth_m"))
                existing["last_seen"] = m.get("last_seen", existing.get("last_seen"))
                existing["source"] = m.get("source", existing.get("source"))
            # Always update observation timestamp for TTL expiry.
            self._persistent_markers[mid]["ts"] = time.time()
    def get_persistent_markers(self) -> list[dict]:
        with self._lock:
            return list(self._persistent_markers.values())

    def find_marker_by_label(self, target: str) -> dict | None:
        """Return the best-matching persistent marker for *target*, or None.

        Uses the same fuzzy scoring as recon_movement (substring, token
        overlap, plural stripping) so "plant" matches "potted plant".
        """
        from skills.recon_movement import _target_score  # noqa: PLC0415

        markers = self.get_persistent_markers()
        if not markers:
            return None
        scored = [
            (_target_score(m.get("label", ""), target), m)
            for m in markers
        ]
        scored = [(s, m) for s, m in scored if s > 0]
        if not scored:
            return None
        # Best label match; break ties with most-recently-seen.
        return max(scored, key=lambda item: (item[0], item[1].get("last_seen", 0)))[1]

    def navigate_to_pose(self, x: float, y: float, theta: float = 0.0) -> bool:
        """Send a Nav2 NavigateToPose goal.  Returns True if the goal was sent."""
        try:
            from rclpy.action import ActionClient          # noqa: PLC0415
            from nav2_msgs.action import NavigateToPose     # noqa: PLC0415
            from geometry_msgs.msg import PoseStamped       # noqa: PLC0415

            if not hasattr(self, "_nav2_client"):
                self._nav2_client = ActionClient(
                    self, NavigateToPose, "/navigate_to_pose"
                )

            if not self._nav2_client.wait_for_server(timeout_sec=2.0):
                self.get_logger().warn("Nav2 action server not available")
                return False

            goal = NavigateToPose.Goal()
            goal.pose = PoseStamped()
            goal.pose.header.frame_id = "map"
            goal.pose.header.stamp = self.get_clock().now().to_msg()
            goal.pose.pose.position.x = x
            goal.pose.pose.position.y = y
            goal.pose.pose.orientation.z = math.sin(theta / 2.0)
            goal.pose.pose.orientation.w = math.cos(theta / 2.0)

            future = self._nav2_client.send_goal_async(goal)
            self.get_logger().info(
                f"[NAV2] goal sent: ({x:.2f}, {y:.2f}, θ={math.degrees(theta):.0f}°)"
            )
            future.add_done_callback(self._on_nav2_goal_response)
            return True
        except Exception as e:
            self.get_logger().warn(f"Nav2 goal failed: {e}")
            return False

    def _on_nav2_goal_response(self, future) -> None:
        try:
            goal_handle = future.result()
        except Exception as e:
            self.get_logger().error(f"[NAV2] goal send FAILED: {e}")
            return
        if not goal_handle.accepted:
            self.get_logger().warn("[NAV2] goal REJECTED by Nav2")
            return
        self.get_logger().info("[NAV2] goal ACCEPTED — robot should be moving")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_nav2_result)

    def _on_nav2_result(self, future) -> None:
        try:
            result = future.result()
            self.get_logger().info(f"[NAV2] navigation finished, status={result.status}")
        except Exception as e:
            self.get_logger().warn(f"[NAV2] navigation result error: {e}")

    def clear_persistent_markers(self) -> None:
        with self._lock:
            self._persistent_markers.clear()
        self.get_logger().info("persistent marker store cleared")

    # ------------------------------------------------------------------
    # Diagnostic helpers
    # ------------------------------------------------------------------

    def _check_diagnostics(self) -> None:
        """Log one-time warnings for missing sensor topics after startup."""
        elapsed = time.time() - self._start_time
        if elapsed < 10.0:
            return
        with self._lock:
            has_map = self._last_map is not None
            has_depth = self._last_depth_m is not None
            has_cam = self._camera_info is not None

        if not has_map and not self._warned_no_map:
            self._warned_no_map = True
            self.get_logger().warn(
                "no /map received — SLAM not running; occupancy grid will be empty"
            )
        if not has_depth and not self._warned_no_depth:
            self._warned_no_depth = True
            self.get_logger().warn(
                "no depth image received — VLM markers will use assumed depths"
            )
        if not has_cam and not self._warned_no_camera_info:
            self._warned_no_camera_info = True
            self.get_logger().warn(
                "no camera_info received — VLM bearing uses fallback FOV estimate"
            )

    # ------------------------------------------------------------------
    # Pose tracking
    # ------------------------------------------------------------------

    def _store_pose(self, x: float, y: float, theta: float, source: str) -> None:
        with self._lock:
            first = self._pose is None
            self._pose = (x, y, theta)
        if first:
            self.get_logger().info(
                f"first pose from {source}: x={x:.3f} y={y:.3f} theta={theta:.3f}"
            )

    def _try_activate_slam(self) -> None:
        """Auto-activate slam_toolbox lifecycle node (configure → activate)."""
        if self._slam_activated:
            return
        if not self._slam_lifecycle_change.service_is_ready():
            self.get_logger().info("[SLAM-ACTIVATE] waiting for /slam_toolbox/change_state service...")
            return
        if not self._slam_lifecycle_get.service_is_ready():
            return

        # Check current state first
        get_req = GetState.Request()
        future = self._slam_lifecycle_get.call_async(get_req)
        future.add_done_callback(self._on_slam_state_response)

    def _on_slam_state_response(self, future) -> None:
        try:
            resp = future.result()
        except Exception as e:
            self.get_logger().warn(f"[SLAM-ACTIVATE] get_state failed: {e}")
            return
        state_id = resp.current_state.id
        state_label = resp.current_state.label
        self.get_logger().info(f"[SLAM-ACTIVATE] slam_toolbox state: {state_label} (id={state_id})")

        if state_label == "active":
            self._slam_activated = True
            self.get_logger().info("[SLAM-ACTIVATE] slam_toolbox already active!")
            return

        # Determine which transition to send
        if state_label == "unconfigured":
            transition_id = Transition.TRANSITION_CONFIGURE
            label = "configure"
        elif state_label == "inactive":
            transition_id = Transition.TRANSITION_ACTIVATE
            label = "activate"
        else:
            self.get_logger().warn(f"[SLAM-ACTIVATE] unexpected state {state_label}, skipping")
            return

        req = ChangeState.Request()
        req.transition = Transition()
        req.transition.id = transition_id
        self.get_logger().info(f"[SLAM-ACTIVATE] sending '{label}' transition...")
        future = self._slam_lifecycle_change.call_async(req)
        future.add_done_callback(
            lambda f: self._on_slam_transition_done(f, label)
        )

    def _on_slam_transition_done(self, future, label: str) -> None:
        try:
            resp = future.result()
        except Exception as e:
            self.get_logger().warn(f"[SLAM-ACTIVATE] {label} failed: {e}")
            return
        if resp.success:
            self.get_logger().info(f"[SLAM-ACTIVATE] '{label}' succeeded!")
            if label == "activate":
                self._slam_activated = True
                self.get_logger().info("[SLAM-ACTIVATE] slam_toolbox is now ACTIVE — live mapping enabled")
        else:
            self.get_logger().warn(f"[SLAM-ACTIVATE] '{label}' returned success=False")

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
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        w, h = msg.info.width, msg.info.height
        with self._lock:
            # Always accept the newest map — slam_toolbox publishes to /map
            # directly when active, overriding the stale navigation_map_server.
            if stamp > self._last_map_stamp:
                self.get_logger().info(
                    f"[MAP-DEBUG] /map ACCEPTED {w}x{h} stamp={stamp:.1f}"
                )
                self._last_map = msg
                self._last_map_stamp = stamp

    def _poll_map(self) -> None:
        """Timer callback: request the latest map from slam_toolbox."""
        if self._map_poll_pending:
            return
        if not self._dynamic_map_cli.service_is_ready():
            return
        self._map_poll_pending = True
        future = self._dynamic_map_cli.call_async(GetMap.Request())
        future.add_done_callback(self._on_dynamic_map_response)

    def _on_dynamic_map_response(self, future) -> None:
        self._map_poll_pending = False
        try:
            resp = future.result()
        except Exception:
            return
        if resp and resp.map and resp.map.info.width > 0:
            stamp = resp.map.header.stamp.sec + resp.map.header.stamp.nanosec * 1e-9
            w, h = resp.map.info.width, resp.map.info.height
            with self._lock:
                self._last_map = resp.map
                self._last_map_stamp = stamp
            self.get_logger().info(f"[MAP-DEBUG] dynamic_map got {w}x{h} stamp={stamp:.1f}")

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

    def _approach_state_cb(self, msg: String) -> None:
        try:
            import json as _json
            data = _json.loads(msg.data)
            with self._lock:
                self._approach_state = data
                self._approach_state_ts = time.time()
        except Exception:
            pass

    def get_image_b64(self) -> str | None:
        """Return the latest camera frame as base64, or None if no frame yet."""
        import base64
        with self._lock:
            if self._last_image_bytes is None:
                return None
            return base64.b64encode(self._last_image_bytes).decode()

    def set_vlm_result(self, result: dict) -> None:
        now = time.time()
        with self._lock:
            self._vlm_result = result
            self._vlm_result_ts = now
            # Publish fresh annotations to the shared ROS topic so skills can
            # read the pre-computed VLM result instead of calling Gemini inline.
            try:
                import json as _json
                from std_msgs.msg import String as _String  # noqa: PLC0415
                annotations = result.get("annotations", [])
                if hasattr(self, "_vlm_annotations_pub"):
                    payload = _json.dumps({"annotations": annotations, "ts": now})
                    self._vlm_annotations_pub.publish(_String(data=payload))
            except Exception:
                pass
            annotations = result.get("annotations", [])
            depth_m = self._last_depth_m
            pose = self._pose
            camera_info = dict(self._camera_info) if self._camera_info else None

        if pose is not None and annotations:
            self.get_logger().info(
                f"[VLM-DEPTH] projecting {len(annotations)} annotations | "
                f"pose=({pose[0]:.2f}, {pose[1]:.2f}, θ={pose[2]:.2f}) | "
                f"depth_image={'YES' if depth_m is not None else 'NO'} | "
                f"camera_info={'YES' if camera_info else 'NO'}"
            )
            new_markers = markers_from_annotations(
                annotations,
                depth_m,
                pose,
                camera_info=camera_info,
                now=now,
            )
            for m in new_markers:
                self.get_logger().info(
                    f"[VLM-MARKER] {m['label']:20s} → "
                    f"world=({m['x']:.2f}, {m['y']:.2f}) "
                    f"depth={m['depth_m']:.2f}m "
                    f"bearing={m['bearing_rad']:.3f}rad "
                    f"source={m['source']}"
                )
            with self._lock:
                self._merge_into_store(new_markers)

    def get_vlm_result(self) -> dict:
        with self._lock:
            return dict(self._vlm_result)

    # -- Autonomy --------------------------------------------------------

    def set_autonomy(self, enabled: bool) -> None:
        if enabled and not AUTONOMY_SWITCHING_ENABLED and not self._mission_running:
            self.get_logger().info("autonomy enable ignored: autonomous switching disabled")
            return
        with self._lock:
            self._autonomy_enabled = enabled
        self.get_logger().info(f"autonomy {'ENABLED' if enabled else 'DISABLED'}")

    def start_mission(self) -> None:
        """Activate the autonomous bomb-disposal mission."""
        self._mission_running = True
        self.set_autonomy(True)
        self.set_planner_phase("scanning")
        self.get_logger().info("[MISSION] autonomous bomb-disposal mission STARTED")

    def stop_mission(self) -> None:
        """Abort the autonomous mission."""
        self._mission_running = False
        self.set_autonomy(False)
        self.set_planner_phase("idle")
        self.stop_manual_motion()
        self.get_logger().info("[MISSION] mission STOPPED")

    def broadcast_mission_phase(self, phase: str) -> None:
        """Push a mission_update message to all WS clients via the broadcast fn."""
        if self._mission_broadcast_fn:
            try:
                self._mission_broadcast_fn(phase)
            except Exception:
                pass

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

    def speak(self, text: str) -> bool:
        """Speak text via ElevenLabs TTS. Returns False if TTS is unavailable."""
        with self._lock:
            tts = self._tts
        if tts is None:
            return False
        tts.speak_async(text)
        return True

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

    # Words that signal a conditional or goal-directed command — let these
    # fall through to the brain rather than executing as a fixed-duration move.
    _CONDITIONAL_WORDS: frozenset = frozenset({
        "until", "while", "when", "unless", "keep", "continue",
        "see", "find", "spot", "detect", "notice", "reach",
    })

    def _parse_manual_motion(self, command: str) -> tuple[str, float, float, float] | None:
        import re as _re
        tokens = command.split()
        self.get_logger().info(f"[CMD] _parse_manual_motion tokens={tokens}")

        # Goal-directed or conditional commands belong to the brain.
        if any(w in tokens for w in self._CONDITIONAL_WORDS):
            self.get_logger().info("[CMD] → conditional word detected, routing to brain")
            return None

        # Degree-based turn: "turn 90 degrees left", "rotate 180 ccw", etc.
        # Parsed before the token-count gate so multi-word turn commands work.
        _turn_match = _re.search(
            r"(\d+(?:\.\d+)?)\s*(?:deg(?:rees?)?|°)?",
            command,
        )
        if _turn_match and any(w in tokens for w in (
            "turn", "rotate", "spin", "pivot",
        )):
            _deg = float(_turn_match.group(1))
            _rad = math.radians(_deg)
            _ccw = not any(w in tokens for w in ("right", "clockwise", "cw"))
            _ang = _MANUAL_TURN_RADPS if _ccw else -_MANUAL_TURN_RADPS
            _dur = min(_rad / _MANUAL_TURN_RADPS, _MANUAL_MAX_DURATION_S)
            _label = f"rotate {_deg:.0f}° {'CCW' if _ccw else 'CW'}"
            self.get_logger().info(f"[CMD] → matched TURN {_deg}° ({'CCW' if _ccw else 'CW'}), dur={_dur:.2f}s")
            return _label, 0.0, _ang, _dur

        # More than 4 tokens is almost certainly natural language, not a simple move.
        if len(tokens) > 4:
            self.get_logger().info("[CMD] → too many tokens (>4), routing to brain")
            return None

        duration = _MANUAL_DEFAULT_DURATION_S
        for token in tokens:
            try:
                duration = max(0.1, min(float(token), _MANUAL_MAX_DURATION_S))
                break
            except ValueError:
                continue

        if any(word in tokens for word in ("forward", "ahead")):
            self.get_logger().info(f"[CMD] → matched FORWARD, duration={duration}")
            return "forward", _MANUAL_FORWARD_MPS, 0.0, duration
        if any(word in tokens for word in ("back", "backward", "backwards", "reverse")):
            self.get_logger().info(f"[CMD] → matched BACK, duration={duration}")
            return "back", _MANUAL_BACKWARD_MPS, 0.0, duration
        if "left" in tokens:
            self.get_logger().info(f"[CMD] → matched LEFT, duration={duration}")
            return "left", 0.0, _MANUAL_TURN_RADPS, duration
        if "right" in tokens:
            self.get_logger().info(f"[CMD] → matched RIGHT, duration={duration}")
            return "right", 0.0, -_MANUAL_TURN_RADPS, duration
        self.get_logger().info(f"[CMD] → no motion keyword matched in {tokens}")
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
            "ranges": [
                float(r) if math.isfinite(r) else None
                for r in scan.ranges
            ],
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
    # detector, tts = _init_intruder_alert()  # voice alerts disabled
    # if tts is not None:
    #     with node._lock:
    #         node._tts = tts
    detector, tts = None, None
    print("[VLM] VLM thread started.")

    _vlm_cycle = 0
    while True:
        time.sleep(VLM_INTERVAL)
        _vlm_cycle += 1
        image_b64 = node.get_image_b64()
        if image_b64 is None:
            if _vlm_cycle <= 5 or _vlm_cycle % 10 == 0:
                print(f"[VLM] cycle {_vlm_cycle}: no camera frame — skipping")
            continue
        try:
            planner_phase = node.get_planner_phase()
            print(f"[VLM] cycle {_vlm_cycle}: got frame ({len(image_b64)} bytes), phase={planner_phase}, calling Gemini…")
            if planner_phase in ("approach", "approaching_bomb", "defusing"):
                # Bypass VLMSession: call defusal prompt directly so the
                # defusal/wires keys are NOT stripped before reaching the dashboard.
                result = analyze_frame(image_b64, phase="defusal")
            else:
                # "recon" or "done": use session for cumulative rooms tracking.
                result = session.update(image_b64)
            annotations = result.get("annotations", [])
            print(f"[VLM] cycle {_vlm_cycle}: Gemini returned {len(annotations)} annotations")
            node.set_vlm_result(result)

            if detector and tts:
                _handle_intruder_alert(result, detector, tts)
        except Exception as exc:
            import traceback
            print(f"[VLM] cycle {_vlm_cycle} ERROR: {exc}")
            traceback.print_exc()


async def serve(node: MapStreamNode, host: str, port: int, radar: RadarListener | None = None) -> None:
    import websockets
    from websockets.asyncio.server import Response
    from websockets.datastructures import Headers
    try:
        from slam.command_executor import CommandExecutor
        from slam.command_router import ReconCommandRouter, STOP_COMMANDS, normalize_command
    except ModuleNotFoundError as exc:  # pragma: no cover - script execution fallback.
        if exc.name != "slam":
            raise
        from command_executor import CommandExecutor
        from command_router import ReconCommandRouter, STOP_COMMANDS, normalize_command

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
    command_router = ReconCommandRouter(node, broadcast_status)

    loop = asyncio.get_event_loop()

    def _mission_phase_bridge(phase: str) -> None:
        """Thread-safe bridge to send mission_update to all WS clients."""
        async def _do():
            payload = json.dumps({"type": "mission_update", "phase": phase})
            stale = []
            for c in list(clients):
                try:
                    await c.send(payload)
                except Exception:
                    stale.append(c)
            for c in stale:
                clients.discard(c)
        loop.call_soon_threadsafe(asyncio.ensure_future, _do())

    node._mission_broadcast_fn = _mission_phase_bridge

    # Brain chat bridge — receives /brain/chat_out from the ROS callback thread
    # and broadcasts it to all dashboard WebSocket clients.
    chat_out_queue: asyncio.Queue = asyncio.Queue()
    node.set_chat_loop(chat_out_queue, asyncio.get_event_loop())

    async def brain_chat_drainer() -> None:
        while True:
            entry = await chat_out_queue.get()
            sender = entry.get("sender", "robot")
            text = str(entry.get("text") or "").strip()
            if not text:
                continue
            # Map sender → dashboard phase.
            if sender in ("robot_thoughts", "robot_anticipation"):
                phase = "planning"
            elif sender == "skill_status":
                phase = "executing"
            elif sender == "system":
                phase = "done"
            else:
                phase = "bot"
            await broadcast_status({"phase": phase, "text": text})

    asyncio.create_task(brain_chat_drainer())

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
                if msg.get("cmd") == "start_mission":
                    node.start_mission()
                    await broadcast_status({"phase": "scanning", "text": "Mission started"})
                elif msg.get("cmd") == "stop_mission":
                    node.stop_mission()
                    await broadcast_status({"phase": "idle", "text": "Mission aborted"})
                elif msg.get("cmd") == "set_autonomy":
                    enabled = bool(msg.get("enabled", False))
                    node.set_autonomy(enabled)
                    if enabled and not AUTONOMY_SWITCHING_ENABLED:
                        await ws.send(json.dumps({
                            "type": "status",
                            "phase": "error",
                            "text": "Autonomous switching is disabled; use manual commands",
                        }))
                elif msg.get("cmd") == "operator_command":
                    text = str(msg.get("text", "")).strip()
                    if await command_router.handle(text, node):
                        if normalize_command(text) in STOP_COMMANDS:
                            await command_executor.stop()
                    else:
                        status, is_error = node.handle_operator_command(text)
                        await ws.send(json.dumps({
                            "type": "status",
                            "phase": "error" if is_error else "done",
                            "text": status,
                        }))
                elif msg.get("type") == "action":
                    text = str(msg.get("text", "")).strip()
                    node.get_logger().info(f"[CMD] received action: '{text}'")
                    if not text:
                        await ws.send(json.dumps({
                            "type": "status",
                            "phase": "error",
                            "text": "empty command",
                        }))
                        continue

                    router_handled = await command_router.handle(text, node)
                    node.get_logger().info(f"[CMD] command_router handled={router_handled}")
                    if router_handled:
                        if normalize_command(text) in STOP_COMMANDS:
                            await command_executor.stop()
                        continue

                    status, is_error = node.handle_operator_command(text)
                    node.get_logger().info(f"[CMD] handle_operator_command → status='{status}' is_error={is_error}")
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

                    # Route to the PEAS cloud agent (recon_agent) via brain/chat_in.
                    node.activate_agent("recon_agent")
                    node.publish_chat_in(text)
                    await broadcast_status({"phase": "planning", "text": f"→ {text}"})
                elif msg.get("type") == "stop":
                    node.set_autonomy(False)
                    node.stop_manual_motion()
                    await command_router.stop()
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
            current_phase = node.get_planner_phase() if node._mission_running else "idle"
            payload: dict = {
                "timestamp": time.time(),
                "mission_phase": current_phase,
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
            payload["semantic_markers"] = node.get_persistent_markers()
            if radar is not None:
                payload["radar_targets"] = radar.get_world_targets(pose)
            payload["autonomy"] = node.get_planner_state()
            # Approach telemetry — only include when fresh (within 2 s).
            with node._lock:
                ap_state = dict(node._approach_state)
                ap_ts = node._approach_state_ts
            if ap_state and (time.time() - ap_ts) < 2.0:
                payload["approach"] = ap_state
            node._check_diagnostics()
            # Only consume the alert when there are clients — if no browser is
            # connected the alert would be cleared and permanently lost.
            alert = node.get_and_clear_alert() if clients else None
            if alert is not None:
                payload["alert"] = alert

            if clients:
                msg = json.dumps(payload)
                if "Infinity" in msg or "NaN" in msg:
                    msg = msg.replace("-Infinity", "null").replace("Infinity", "null").replace("NaN", "null")
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
_MANUAL_DEFAULT_DURATION_S = 1.5
_MANUAL_MAX_DURATION_S = 5.0
_MANUAL_FORWARD_MPS = 0.16
_MANUAL_BACKWARD_MPS = -0.12
_MANUAL_TURN_RADPS = 0.6


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
    """Background thread: runs the MissionPlanner FSM when a mission is active.

    The thread runs continuously. When no mission is active it idles.
    When a mission starts (via start_mission), it drives the full FSM:
    scanning → person_detected → approaching_person → evacuating → searching
    → bomb_detected → approaching_bomb → defusing → done.
    """
    try:
        from vlm.planner import MissionPlanner
    except ImportError:
        print("[Planner] vlm module not found — planner thread disabled.")
        return

    planner = MissionPlanner()
    print("[Planner] Planner thread started (waiting for mission).")
    last_phase = ""

    while True:
        if not node._mission_running:
            time.sleep(0.5)
            planner.reset()
            last_phase = ""
            continue

        vlm_result = node.get_vlm_result()
        if not vlm_result:
            time.sleep(1.0)
            continue

        with node._lock:
            result_age = time.time() - node._vlm_result_ts
        if result_age > VLM_INTERVAL * 2:
            vlm_result = {**vlm_result,
                          "threat_detected": False,
                          "annotations": [],
                          "defusal": {}}

        # Augment with depth data for approach phases
        if planner.phase in ("approaching_person", "approaching_bomb"):
            cat = "person" if planner.phase == "approaching_person" else "threat"
            target = planner._find_target(vlm_result, cat)
            if target:
                try:
                    depth = node.get_depth_at_bbox(target["bbox"])
                except Exception:
                    depth = None
                if depth is not None:
                    vlm_result = {**vlm_result, "_threat_depth_m": depth}

        cmd = planner.next_command(vlm_result)
        node.set_pending_command(cmd)
        node.set_planner_phase(planner.phase)

        # Broadcast phase changes to dashboard
        if planner.phase != last_phase:
            last_phase = planner.phase
            node.broadcast_mission_phase(planner.phase)
            print(f"[MISSION] phase → {planner.phase}")

        if cmd.kind == "done":
            node.set_alert(cmd.reason)
            node.broadcast_mission_phase("done")
            node._mission_running = False
            node.set_autonomy(False)
            node.set_planner_phase("done")
            planner.reset()
            print(f"[MISSION] COMPLETE: {cmd.reason}")
            time.sleep(1.0)
        elif cmd.kind == "speak":
            # TTS evacuation warning
            tts = getattr(node, "_tts", None)
            if tts is not None:
                try:
                    tts.speak_async(cmd.reason)
                except Exception as exc:
                    print(f"[MISSION] TTS error: {exc}")
            time.sleep(cmd.duration)
        elif cmd.kind == "defuse":
            # Publish wire-cut action
            from std_msgs.msg import String as _String  # noqa: PLC0415
            wire_color = cmd.reason.replace("cut ", "").strip()
            node._defusal_action_pub.publish(_String(data=f"cut {wire_color}"))
            print(f"[MISSION] defuse action: cut {wire_color}")
            time.sleep(cmd.duration)
        else:
            _execute_command(node, cmd)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--depth-topic", default=DEFAULT_DEPTH_TOPIC)
    ap.add_argument("--camera-info-topic", default=DEFAULT_CAMERA_INFO_TOPIC)
    ap.add_argument("--depth-scale", type=float, default=0.001)
    ap.add_argument(
        "--radar-serial",
        nargs="*",
        metavar="NODE=PORT",
        help="ESP serial ports, e.g. A=/dev/ttyUSB0 B=/dev/ttyUSB1",
    )
    ap.add_argument("--radar-udp-port", type=int, default=RADAR_UDP_PORT)
    args = ap.parse_args()

    # Parse radar serial port mapping — default to auto-detecting both ESPs.
    if args.radar_serial:
        radar_serial_ports: dict[str, str] = {}
        for pair in args.radar_serial:
            node_id, port = pair.split("=", 1)
            radar_serial_ports[node_id] = port
    else:
        radar_serial_ports = {"A": "AUTO", "B": "AUTO"}

    radar = RadarListener(
        serial_ports=radar_serial_ports,
        udp_port=args.radar_udp_port,
    )

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
        asyncio.run(serve(node, args.host, args.port, radar=radar))
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
