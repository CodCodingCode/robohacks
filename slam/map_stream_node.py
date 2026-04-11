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
from sensor_msgs.msg import BatteryState, LaserScan
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"

POSE_HZ = 10.0
MAP_HZ = 1.0
# LiDAR fallback when /map is empty (large messages — keep slow).
SCAN_HZ = 0.5


def _yaw_from_quat(qx: float, qy: float, qz: float, qw: float) -> float:
    return math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))


class MapStreamNode(Node):
    """Tracks the latest robot pose (from whichever pose topic wins) and map."""

    def __init__(self) -> None:
        super().__init__("map_stream_node")
        self._lock = threading.Lock()
        # Store pose as a normalized (x, y, theta) tuple regardless of which
        # topic it came from. `None` until we see our first frame.
        self._pose: tuple[float, float, float] | None = None
        self._last_map: OccupancyGrid | None = None
        self._last_scan: LaserScan | None = None
        self._battery_pct: float | None = None

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

        self.get_logger().info(
            "map_stream_node subscribed to /pose, /odom, /mapping_pose, /map, "
            "/battery_state, /scan"
        )

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
            await ws.wait_closed()
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()

    rclpy.init()
    node = MapStreamNode()

    # rclpy.spin in a dedicated thread so asyncio owns the main thread.
    spin_thread = threading.Thread(
        target=lambda: rclpy.spin(node), daemon=True
    )
    spin_thread.start()

    try:
        asyncio.run(serve(node, args.host, args.port))
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
