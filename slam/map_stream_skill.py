"""MapStreamSkill — stream Innate SLAM output to the dashboard over WebSocket.

This is an Innate `Skill` that reads the robot's built-in SLAM map and
odometry via the documented `RobotState` descriptor (auto-updated at 50 Hz
by the brain_client — see INNATE_DOCS.md §"Robot State"), converts each
frame into the JSON shape consumed by ../dashboard/, and broadcasts it
over a WebSocket server at ws://0.0.0.0:8000/ws.

While the stream runs, the skill also nudges the robot forward/rotates it
via the non-blocking `mobility.send_cmd_vel` so you can watch the map
fill in in real time. Set `drive=False` to stream without moving.

Prerequisites (run once on the robot before invoking this skill):

    ros2 service call /change_navigation_mode \\
        brain_messages/srv/ChangeNavigationMode "{mode: mapping}"

Otherwise LAST_MAP will not update. See slam/README.md for the full
runbook.

Dashboard contract
------------------
Top-level JSON keys (all optional — applyState() does a shallow merge,
so you can send just `robot` at high rate and just `slam` at low rate):

    {
      "timestamp":      float,
      "mission_phase":  "recon",
      "robot": {"x": m, "y": m, "theta": rad, "battery": 0..100},
      "slam":  {"map": {
          "width":      int,
          "height":     int,
          "resolution": float (m/cell),
          "origin":     {"x": m, "y": m},
          "data":       [int, ...]   # ROS OccupancyGrid: -1 unknown, 0 free, 100 occupied
      }}
    }

Fields `slam.map.*` map 1:1 to nav_msgs/OccupancyGrid so no geometric
transformation is needed — the dashboard renders in the same `map` frame
the Innate SLAM publishes in.
"""

from __future__ import annotations

import asyncio
import base64
import json
import math
import threading
import time

import numpy as np

from brain_client.skill_types import (
    Skill,
    SkillResult,
    Interface,
    InterfaceType,
    RobotState,
    RobotStateType,
)


def _yaw_from_quat(qx: float, qy: float, qz: float, qw: float) -> float:
    """Extract yaw (rotation around Z) from a unit quaternion, in radians."""
    return math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))


# Stream rates — the dashboard render loop is 10 FPS (see dashboard/app.js),
# so sending pose faster than that is wasted work. Maps are large and change
# slowly, so push them at ~1 Hz.
POSE_HZ = 10.0
MAP_HZ = 1.0

WS_HOST = "0.0.0.0"
WS_PORT = 8001


class MapStreamSkill(Skill):
    """Stream live SLAM + odometry to the dashboard while the robot drives."""

    # Declared RobotState attributes are auto-populated at 50 Hz by the
    # brain_client while execute() runs. Always None-check on first access.
    map_data = RobotState(RobotStateType.LAST_MAP)
    odom = RobotState(RobotStateType.LAST_ODOM)

    # MobilityInterface — send_cmd_vel is non-blocking (unlike rotate()),
    # so we can nudge the robot inside the stream loop without stalling.
    mobility = Interface(InterfaceType.MOBILITY)

    @property
    def name(self) -> str:
        return "map_stream"

    def guidelines(self) -> str:
        return (
            "Stream the live SLAM occupancy grid and robot pose to the "
            "operator dashboard over ws://:8000/ws. Use during recon or "
            "mapping runs when the operator needs to watch the map build "
            "in real time."
        )

    # ------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------

    def execute(self, duration: float = 300.0, drive: bool = True):
        """Run the WebSocket bridge for `duration` seconds.

        Args:
            duration: How long to stream, in seconds. Default 5 minutes.
            drive:    If True, issue a slow forward+turn nudge every tick
                      so the robot explores while we stream. If False,
                      stream only (useful for static rendering tests).
        """
        self._cancelled = False

        # Lazy import so a missing `websockets` package doesn't break the
        # brain_client at module-load time.
        try:
            import websockets
        except ImportError as exc:
            return (
                f"websockets not installed ({exc}). "
                "Run: pip install websockets",
                SkillResult.FAILURE,
            )

        clients: set = set()
        loop = asyncio.new_event_loop()
        stop = threading.Event()

        async def handler(ws, path=None):
            # Accept any path — dashboard connects to /ws but we don't
            # care. Hold the connection open until the client disconnects.
            clients.add(ws)
            self._send_feedback(f"client connected ({len(clients)} total)")
            try:
                await ws.wait_closed()
            finally:
                clients.discard(ws)
                self._send_feedback(f"client disconnected ({len(clients)} total)")

        async def serve():
            async with websockets.serve(handler, WS_HOST, WS_PORT):
                while not stop.is_set():
                    await asyncio.sleep(0.05)

        def run_loop():
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(serve())
            finally:
                loop.close()

        server_thread = threading.Thread(target=run_loop, daemon=True)
        server_thread.start()
        self._send_feedback(f"websocket server listening on ws://{WS_HOST}:{WS_PORT}/ws")

        # Give the event loop a moment to start accepting connections
        # before we begin broadcasting.
        time.sleep(0.1)

        def broadcast(payload: dict) -> None:
            """Thread-safe fan-out to every connected WebSocket client."""
            if not clients:
                return
            msg = json.dumps(payload)

            async def _send_all():
                # Snapshot clients first — the set can mutate mid-iteration
                # when handler() removes a disconnected client.
                targets = list(clients)
                await asyncio.gather(
                    *(c.send(msg) for c in targets),
                    return_exceptions=True,
                )

            fut = asyncio.run_coroutine_threadsafe(_send_all(), loop)
            try:
                fut.result(timeout=0.1)
            except Exception:
                # Slow / disconnected client — don't let it stall the loop.
                pass

        start = time.time()
        last_map_push = 0.0
        pose_interval = 1.0 / POSE_HZ
        map_interval = 1.0 / MAP_HZ

        try:
            while time.time() - start < duration:
                if self._cancelled:
                    return "Stream cancelled", SkillResult.CANCELLED

                payload: dict = {
                    "timestamp": time.time(),
                    "mission_phase": "recon",
                }

                # --- pose (every tick) -------------------------------------
                # The skills_action_server injects LAST_ODOM as a dict (not
                # an Odometry message). See skills_action_server.py ~l.786.
                odom = self.odom
                if isinstance(odom, dict):
                    try:
                        p = odom["pose"]["pose"]["position"]
                        q = odom["pose"]["pose"]["orientation"]
                        payload["robot"] = {
                            "x": p["x"],
                            "y": p["y"],
                            "theta": _yaw_from_quat(q["x"], q["y"], q["z"], q["w"]),
                            "battery": 100,
                        }
                    except (KeyError, TypeError):
                        pass

                # --- map (every ~1s, shallow-merge won't clobber pose) -----
                # LAST_MAP is injected as a dict with `data_b64` (base64 int8).
                now = time.time()
                map_data = self.map_data
                if isinstance(map_data, dict) and (now - last_map_push) >= map_interval:
                    try:
                        info = map_data["info"]
                        raw = base64.b64decode(map_data["data_b64"])
                        arr = np.frombuffer(raw, dtype=np.int8)
                        payload["slam"] = {
                            "map": {
                                "width": info["width"],
                                "height": info["height"],
                                "resolution": info["resolution"],
                                "origin": {
                                    "x": info["origin"]["position"]["x"],
                                    "y": info["origin"]["position"]["y"],
                                },
                                "data": arr.tolist(),
                            }
                        }
                        last_map_push = now
                    except (KeyError, TypeError, ValueError) as exc:
                        self._send_feedback(f"map decode error: {exc}")

                broadcast(payload)

                # --- nudge the robot so the map grows ---------------------
                if drive:
                    # Slow forward creep with a gentle constant turn — enough
                    # to fill in new cells without running into walls on
                    # every loop. send_cmd_vel returns immediately.
                    self.mobility.send_cmd_vel(
                        linear_x=0.08,
                        angular_z=0.15,
                        duration=0.3,
                    )

                time.sleep(pose_interval)
        finally:
            stop.set()

        return "Stream complete", SkillResult.SUCCESS

    def cancel(self) -> str:
        self._cancelled = True
        return "Stream cancel requested"
