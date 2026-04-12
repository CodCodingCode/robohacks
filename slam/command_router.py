"""Safe command routing for dashboard operator text.

Routes known meta-commands (stop, speak, abort, autonomy) locally.
Everything else returns "fallback" so map_stream_node can forward it
to the PEAS cloud agent via /brain/chat_in.
"""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

BroadcastFn = Callable[[dict], Awaitable[None]]

STOP_COMMANDS = {"stop", "halt", "emergency stop", "e stop", "estop", "hold", "pause"}
AUTONOMY_ENABLE_COMMANDS = {"autonomy on", "enable autonomy", "auto on"}
AUTONOMY_DISABLE_COMMANDS = {"autonomy off", "disable autonomy", "auto off"}


@dataclass(frozen=True)
class CommandRoute:
    kind: str
    text: str


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
    return CommandRoute("fallback", "Forward to brain agent")


class ReconCommandRouter:
    def __init__(self, node: Any, broadcast: BroadcastFn) -> None:
        self._node = node
        self._broadcast = broadcast
        self._stop_event = threading.Event()
        self._task: asyncio.Task | None = None

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
            if node is not None and node.speak(route.text):
                await self._broadcast({"phase": "done", "text": f'Speaking: "{route.text}"'})
            else:
                await self._broadcast({"phase": "error", "text": "TTS unavailable — set ELEVENLABS_API_KEY"})
            return True
        return False

    async def stop(self, message: str = "stop requested", silent: bool = False) -> None:
        self._stop_event.set()
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
