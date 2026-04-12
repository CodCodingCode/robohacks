"""Safe command routing for dashboard operator text.

Routes known meta-commands (stop, speak, abort, autonomy) locally.
Approach commands are executed directly via ReconMovementSkill without
going through the PEAS cloud agent, which is unreliable for real-time use.
Everything else returns "fallback" so map_stream_node can forward it
to the PEAS cloud agent via /brain/chat_in.
"""

from __future__ import annotations

import asyncio
import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

BroadcastFn = Callable[[dict], Awaitable[None]]

STOP_COMMANDS = {"stop", "halt", "emergency stop", "e stop", "estop", "hold", "pause"}
AUTONOMY_ENABLE_COMMANDS = {"autonomy on", "enable autonomy", "auto on"}
AUTONOMY_DISABLE_COMMANDS = {"autonomy off", "disable autonomy", "auto off"}
CLEAR_MAP_COMMANDS = {"clear map", "reset map", "clear markers", "reset markers"}


@dataclass(frozen=True)
class CommandRoute:
    kind: str
    text: str
    target: str = ""
    distance_m: float = 0.0


def normalize_command(text: str) -> str:
    return " ".join(str(text or "").lower().replace("_", " ").split())


def extract_say_text(command: str) -> str:
    """Return the text to speak if this is a 'say ...' command, else empty string."""
    for prefix in ("say ", "announce ", "speak "):
        if command.startswith(prefix):
            return command[len(prefix):].strip()
    return ""


def route_command(text: str) -> CommandRoute:
    command = normalize_command(text)
    if not command:
        return CommandRoute("error", "empty command")
    say_text = extract_say_text(command)
    if say_text:
        return CommandRoute("speak", say_text)
    if command in STOP_COMMANDS:
        return CommandRoute("stop", "Holding position")
    if command in AUTONOMY_ENABLE_COMMANDS:
        return CommandRoute(
            "error",
            "Autonomous switching is disabled; use manual commands",
        )
    if command in AUTONOMY_DISABLE_COMMANDS:
        return CommandRoute("stop", "Autonomy already disabled; holding position")
    if command == "abort":
        return CommandRoute("stop", "Abort received; holding position")
    if command in CLEAR_MAP_COMMANDS:
        return CommandRoute("clear_map", "Map annotations cleared")
    lateral = _extract_lateral_move(command)
    if lateral:
        side, distance_m = lateral
        return CommandRoute(
            "lateral_move",
            f"Moving {side} {distance_m:.2f}m",
            target=side,
            distance_m=distance_m,
        )
    target = _extract_approach_target(command)
    if target:
        return CommandRoute("approach_target", f"Approaching {target}", target=target)
    return CommandRoute("fallback", "Forward to brain agent")


def _extract_lateral_move(command: str) -> tuple[str, float] | None:
    """Return (left/right, distance_m) for lateral reposition commands."""
    match = re.match(
        r"^(?:move|go|shift|drive|walk)\s+(?:to\s+the\s+)?(left|right)\b(.*)$",
        command,
    )
    if not match:
        return None
    side = match.group(1)
    remainder = match.group(2) or ""
    distance_m = 0.5
    distance_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:m|meter|meters|metre|metres)?\b",
        remainder,
    )
    if distance_match:
        distance_m = float(distance_match.group(1))
    return side, distance_m


def _extract_approach_target(command: str) -> str:
    """Extract the core object name from approach commands.

    Strips leading determiners and trailing qualifier clauses so
    'move to that potted plant in front of you' → 'potted plant'
    'move to the chair in your current field of view' → 'chair'
    'approach the office chair on the left' → 'office chair'
    """
    # Strip leading politeness phrases so "can you move to X" still matches.
    command = re.sub(
        r"^(?:can you|could you|please|would you|will you|hey robot|robot)[,\s]+",
        "",
        command,
    )
    patterns = [
        r"^(?:move|go|navigate|drive|walk)\s+(?:to|towards?|toward)\s+(.+)$",
        r"^(?:approach|inspect|reach|find|locate)\s+(.+)$",
    ]
    for pat in patterns:
        m = re.match(pat, command)
        if m:
            raw = m.group(1).strip()

            # Strip leading articles/determiners: "the", "that", "this", "a", "an"
            raw = re.sub(r"^(?:the|that|this|those|these|a|an)\s+", "", raw)

            # Strip trailing qualifier clauses at first qualifying word/phrase
            raw = re.split(
                r"\b(?:"
                r"that(?:'s|s)?\b|which\b|who\b"
                r"|in\s+(?:your|my|front|back|the|this)\b"
                r"|field\s+of\b|point\s+of\s+view\b"
                r"|on\s+the\b|by\s+the\b|next\s+to\b|near\b"
                r"|to\s+the\b|over\s+there\b"
                r"|farther|further|closer"
                r"|right\b|left\b|behind\b|front\b|across\b"
                r")",
                raw,
                maxsplit=1,
            )[0].strip().strip(",")

            # Keep only the first 1-3 meaningful words
            words = raw.split()
            target = " ".join(words[:3]).strip()
            if target and target not in {"area", "room", "wall", "obstacle"}:
                return target
    return ""


# ---------------------------------------------------------------------------
# Direct skill execution (no cloud round-trip)
# ---------------------------------------------------------------------------

class MapStreamMobilityAdapter:
    """Bridges ReconMovementSkill.send_cmd_vel → dedicated /cmd_vel publisher.

    Uses a dedicated rclpy node + SingleThreadedExecutor so it is safe to call
    from any background thread for as long as needed, independent of
    map_stream_node's executor lifecycle.
    """

    def __init__(self, node: Any, stop_event: threading.Event,
                 cmd_vel_pub=None, cmd_vel_lock: threading.Lock | None = None) -> None:
        self._node = node
        self._stop_event = stop_event
        self._cmd_vel_pub = cmd_vel_pub
        self._cmd_vel_lock = cmd_vel_lock or threading.Lock()

    def _publish(self, linear_x: float, angular_z: float) -> bool:
        """Publish one Twist. Returns False if the publisher is unavailable."""
        if self._cmd_vel_pub is not None:
            try:
                from geometry_msgs.msg import Twist  # noqa: PLC0415
                twist = Twist()
                twist.linear.x = float(linear_x)
                twist.angular.z = float(angular_z)
                with self._cmd_vel_lock:
                    self._cmd_vel_pub.publish(twist)
                return True
            except Exception:
                pass
        # Fallback to node's publisher if dedicated one isn't ready.
        try:
            self._node.publish_twist(linear_x, angular_z)
            return True
        except Exception:
            return False

    def send_cmd_vel(self, linear_x: float, angular_z: float, duration: float) -> None:
        duration = max(0.0, min(float(duration), 3.0))
        deadline = time.time() + duration
        while time.time() < deadline and not self._stop_event.is_set():
            if not self._publish(linear_x, angular_z):
                self._stop_event.set()
                return
            time.sleep(0.1)
        # No trailing stop — the next send_cmd_vel or explicit _stop() handles it.
        # Stopping here caused deceleration jitter between every step.


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class ReconCommandRouter:
    def __init__(self, node: Any, broadcast: BroadcastFn) -> None:
        self._node = node
        self._broadcast = broadcast
        self._stop_event = threading.Event()
        self._task: asyncio.Task | None = None
        self._cmd_vel_pub = None
        self._cmd_vel_lock = threading.Lock()
        self._init_cmd_vel_pub()

    def _init_cmd_vel_pub(self) -> None:
        """Create a dedicated rclpy node + SingleThreadedExecutor for /cmd_vel.

        Isolated from map_stream_node's executor so it can publish safely from
        any background thread without context conflicts.
        """
        try:
            import rclpy                                        # noqa: PLC0415
            from rclpy.executors import SingleThreadedExecutor  # noqa: PLC0415
            from geometry_msgs.msg import Twist                 # noqa: PLC0415
            if not rclpy.ok():
                return
            _node = rclpy.create_node("recon_approach_cmd_vel")
            self._cmd_vel_pub = _node.create_publisher(Twist, "/cmd_vel", 10)
            _exe = SingleThreadedExecutor()
            _exe.add_node(_node)
            threading.Thread(target=_exe.spin, daemon=True,
                             name="recon_cmd_vel_spin").start()
        except Exception:
            pass  # rclpy unavailable or already shut down

    async def handle(self, text: str, node: Any = None) -> bool:
        route = route_command(text)
        if route.kind == "fallback":
            return False
        if route.kind == "error":
            await self._broadcast({"phase": "error", "text": route.text})
            return True
        if route.kind == "stop":
            await self.stop(route.text)
            return True
        if route.kind == "speak":
            n = node or self._node
            if n is not None and n.speak(route.text):
                await self._broadcast({"phase": "done", "text": f'Speaking: "{route.text}"'})
            else:
                await self._broadcast({"phase": "error", "text": "TTS unavailable — set ELEVENLABS_API_KEY"})
            return True
        if route.kind == "clear_map":
            n = node or self._node
            if n is not None:
                n.clear_persistent_markers()
            await self._broadcast({"phase": "done", "text": route.text})
            return True
        if route.kind == "lateral_move":
            action = f"move_{route.target}"
            n = node or self._node
            if n is not None:
                n.activate_agent("recon_agent")
                n.publish_chat_in(
                    "Call recon_movement skill with "
                    f"action={action} and distance_m={route.distance_m:.2f}"
                )
            await self._broadcast(
                {
                    "phase": "planning",
                    "text": f"→ moving {route.target} {route.distance_m:.2f}m",
                }
            )
            return True
        if route.kind == "approach_target":
            if self._task is not None and not self._task.done():
                await self._broadcast({"phase": "error", "text": "busy — wait for current movement to finish"})
                return True
            self._stop_event.clear()
            await self._broadcast({"phase": "executing", "text": f"→ approaching {route.target}"})
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._run_approach(route.target))
            return True
        return False

    async def _run_approach(self, target: str) -> None:
        loop = asyncio.get_running_loop()
        try:
            message, status = await loop.run_in_executor(
                None, self._execute_approach, target
            )
            if self._stop_event.is_set():
                await self._broadcast({"phase": "idle", "text": "approach cancelled"})
                return
            phase = "done" if "Arrived" in message or status == "success" else "error"
            await self._broadcast({"phase": phase, "text": message})
        except Exception as exc:
            await self._broadcast({"phase": "error", "text": f"approach failed: {exc}"})

    def _execute_approach(self, target: str) -> tuple[str, str]:
        try:
            from skills.recon_movement import ReconMovementSkill  # noqa: PLC0415
            import skills.recon_movement as _rm                   # noqa: PLC0415
        except ImportError:
            import sys, os  # noqa: PLC0415
            sys.path.insert(0, os.path.expanduser("~/robohacks"))
            from skills.recon_movement import ReconMovementSkill  # noqa: PLC0415
            import skills.recon_movement as _rm                   # noqa: PLC0415

        # Inject current VLM annotations into module-level cache so the skill
        # never tries to spin its own rclpy node (conflicts with map_stream_node).
        try:
            vlm_result = self._node.get_vlm_result() or {}
            annotations = vlm_result.get("annotations", [])
            with _rm._vlm_cache_lock:
                _rm._vlm_cache.update({"annotations": annotations, "ts": time.time()})
        except Exception:
            pass

        # Start background threads that continuously sync VLM + depth data
        # from map_stream_node into the skill's module-level caches.
        sync_stop = threading.Event()

        def _sync_vlm():
            """Keep VLM annotation cache fresh so bearing doesn't go stale."""
            while not sync_stop.is_set():
                try:
                    vlm_result = self._node.get_vlm_result() or {}
                    annotations = vlm_result.get("annotations", [])
                    if annotations:
                        with _rm._vlm_cache_lock:
                            _rm._vlm_cache.update({
                                "annotations": annotations,
                                "ts": time.time(),
                            })
                except Exception:
                    pass
                time.sleep(0.5)  # 2Hz — VLM updates every ~3s anyway

        vlm_thread = threading.Thread(target=_sync_vlm, daemon=True,
                                       name="vlm_sync")
        vlm_thread.start()

        depth_stop = sync_stop  # reuse the same event for both threads

        def _sync_depth():
            while not depth_stop.is_set():
                try:
                    node_lock = getattr(self._node, "_lock", None)
                    if node_lock is not None:
                        with node_lock:
                            depth_m = self._node._last_depth_m
                            cam_info = self._node._camera_info
                    else:
                        depth_m = self._node._last_depth_m
                        cam_info = self._node._camera_info
                    if depth_m is not None:
                        with _rm._depth_lock:
                            _rm._depth_image = depth_m
                            _rm._depth_cam_info = cam_info
                except Exception:
                    pass
                time.sleep(0.05)  # sync at 20 Hz — matches OAK-D publish rate

        depth_thread = threading.Thread(target=_sync_depth, daemon=True,
                                        name="depth_sync")
        depth_thread.start()

        try:
            skill = ReconMovementSkill(
                analyzer=lambda _img: self._node.get_vlm_result() or {},
                sleeper=self._sleep,
            )
            skill.mobility = MapStreamMobilityAdapter(
                self._node, self._stop_event,
                cmd_vel_pub=self._cmd_vel_pub,
                cmd_vel_lock=self._cmd_vel_lock,
            )
            skill.image = self._node.get_image_b64()
            return skill.execute(
                "approach_object",
                target=target,
                max_duration_s=90.0,
            )
        finally:
            depth_stop.set()

    def _sleep(self, duration: float) -> None:
        deadline = time.time() + max(0.0, float(duration))
        while time.time() < deadline and not self._stop_event.is_set():
            time.sleep(min(0.1, deadline - time.time()))

    async def stop(self, message: str = "stop requested", silent: bool = False) -> None:
        self._stop_event.set()
        if self._task is not None and not self._task.done():
            self._task.cancel()
        try:
            self._node.stop_manual_motion()
        except Exception:
            pass
        try:
            self._node.publish_twist(0.0, 0.0)
        except Exception:
            pass
        if not silent:
            await self._broadcast({"phase": "idle", "text": message})
