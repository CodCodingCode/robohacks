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
CLEAR_MAP_COMMANDS = {"clear map", "reset map", "clear markers", "reset markers"}


@dataclass(frozen=True)
class CommandRoute:
    kind: str
    text: str
    target: str = ""


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
    target = _extract_approach_target(command)
    if target:
        return CommandRoute("approach_target", f"Approaching {target}", target=target)
    return CommandRoute("fallback", "Forward to brain agent")


def _extract_approach_target(command: str) -> str:
    """Extract the core object name from approach commands.

    Strips trailing qualifiers so 'move to the chair that's farther away'
    produces 'chair', not 'chair that's farther away'.
    """
    import re

    patterns = [
        r"^(?:move|go|navigate|drive|walk)\s+(?:to|towards?|toward)\s+(?:the\s+)?(.+)$",
        r"^(?:approach|inspect|reach|find|locate)\s+(?:the\s+)?(.+)$",
    ]
    for pat in patterns:
        m = re.match(pat, command)
        if m:
            raw = m.group(1).strip()
            # Strip trailing qualifier clauses: "that's ...", "on the ...", etc.
            raw = re.split(
                r"\b(?:that(?:'s|s)?\b|which\b|who\b|on\s+the\b|in\s+the\b"
                r"|near\b|next\s+to\b|to\s+the\b|by\s+the\b|farther|further"
                r"|closer|right|left|behind|front|across)",
                raw,
                maxsplit=1,
            )[0].strip()
            # Keep only the first 1-3 meaningful words (e.g. "office chair")
            words = raw.split()
            target = " ".join(words[:3]).strip(" ,")
            if target and target not in {"area", "room", "wall", "obstacle"}:
                return target
    return ""


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
        if route.kind == "clear_map":
            if node is not None:
                node.clear_persistent_markers()
            await self._broadcast({"phase": "done", "text": route.text})
            return True
        if route.kind == "approach_target":
            if node is not None:
                node.activate_agent("recon_agent")
                # Send an explicit, unambiguous instruction so the PEAS agent
                # calls approach_object without any conversational hesitation.
                node.publish_chat_in(
                    f"Call recon_movement skill with action=approach_object and target={route.target}"
                )
            await self._broadcast({"phase": "planning", "text": f"→ approaching {route.target}"})
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
