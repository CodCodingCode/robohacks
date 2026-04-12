#!/usr/bin/env python3
"""Standalone SLAM → dashboard WebSocket bridge.

Runs as a plain ROS2 Python node (NOT a brain_client Skill). Subscribes
directly to /odom and /map and streams JSON frames over a WebSocket.

Why standalone instead of the MapStreamSkill approach: the brain_client
skills_action_server runs on a single-threaded rclpy executor, so during
a long-running Skill.execute() call, no subscription callbacks fire —
meaning /odom and /map are never seen. A standalone node with its own
executor doesn't have that problem.

Usage (on the Jetson, after sourcing ROS + workspace):

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
import threading
import time
from pathlib import Path

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
        self._last_depth_m = None
        self._camera_info: dict | None = None
        self._depth_scale = depth_scale
        # Latest VLM result — merged into every broadcaster payload.
        self._vlm_result: dict = {}
        self._vlm_result_ts: float = 0.0
        # Autonomy: operator-controlled toggle for planner execution.
        self._autonomy_enabled: bool = False
        self._pending_cmd: dict = {}  # {"kind": str, "reason": str}

        # /cmd_vel publisher — used by the planner thread when autonomy is on.
        from geometry_msgs.msg import Twist  # noqa: PLC0415
        self._cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)

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
        try:
            import cv2
            import numpy as np
            frame = np.frombuffer(bytes(msg.data), dtype=np.uint8).reshape(
                msg.height, msg.width, -1
            )
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ok:
                with self._lock:
                    self._last_image_bytes = buf.tobytes()
        except Exception as exc:
            self.get_logger().warn(f"image encode failed: {exc}")

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

    def get_semantic_markers(self, now: float) -> list[dict]:
        with self._lock:
            if not self._vlm_result_ts or (now - self._vlm_result_ts) > SEMANTIC_MARKER_TTL:
                return []
            annotations = self._vlm_result.get("annotations", [])
            depth_m = self._last_depth_m
            pose = self._pose
            camera_info = dict(self._camera_info) if self._camera_info else None
        return markers_from_annotations(
            annotations,
            depth_m,
            pose,
            camera_info=camera_info,
            now=now,
        )

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


def run_vlm_thread(node: MapStreamNode) -> None:
    """Background thread: grab camera frames and call Gemini every VLM_INTERVAL seconds.

    Results are stored on the node and merged into the next broadcaster payload.
    Requires GEMINI_API_KEY to be set in the environment.
    """
    import os
    if not os.environ.get("GEMINI_API_KEY"):
        print("[VLM] GEMINI_API_KEY not set — VLM analysis disabled.")
        return

    try:
        from vlm import VLMSession
    except ImportError:
        print("[VLM] vlm module not found — run from repo root or add to PYTHONPATH.")
        return

    session = VLMSession()
    print("[VLM] VLM thread started.")

    while True:
        time.sleep(VLM_INTERVAL)
        image_b64 = node.get_image_b64()
        if image_b64 is None:
            continue
        try:
            result = session.update(image_b64)
            node.set_vlm_result(result)
        except Exception as exc:
            print(f"[VLM] analysis error: {exc}")


async def serve(node: MapStreamNode, host: str, port: int) -> None:
    import websockets
    from websockets.asyncio.server import Response
    from websockets.datastructures import Headers

    clients: set = set()

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
                    node.set_autonomy(bool(msg.get("enabled", False)))
        finally:
            clients.discard(ws)
            node.get_logger().info(f"client disconnected ({len(clients)} total)")

    async def broadcaster() -> None:
        pose_interval = 1.0 / POSE_HZ
        map_interval = 1.0 / MAP_HZ
        scan_interval = 1.0 / SCAN_HZ
        last_map_push = 0.0
        last_scan_push = 0.0
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

            # Merge latest VLM result (rooms, annotations, semantic_plan, etc.)
            vlm = node.get_vlm_result()
            if vlm:
                payload.update(vlm)
            payload["semantic_markers"] = node.get_semantic_markers(now)
            payload["autonomy"] = node.get_planner_state()

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


def _execute_command(node: MapStreamNode, cmd: "RobotCommand") -> None:
    """Translate a RobotCommand into /cmd_vel publishes.

    Blocks for the duration of the command so the planner loop naturally
    waits before requesting the next one.  Aborts early if autonomy is
    disabled mid-command.
    """
    from geometry_msgs.msg import Twist  # noqa: PLC0415

    OMEGA = 0.3  # rad/s used for rotate commands

    def _publish_for(twist: "Twist", duration: float) -> None:
        deadline = time.time() + duration
        while time.time() < deadline:
            if not node.autonomy_enabled:
                break
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

        cmd = planner.next_command(vlm_result)
        node.set_pending_command(cmd)

        if node.autonomy_enabled and cmd.kind != "done":
            _execute_command(node, cmd)
        else:
            # Poll at 1 Hz when idle — fast enough to react to the toggle.
            time.sleep(1.0)


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
