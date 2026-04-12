"""Safe command routing for dashboard operator text.

This module keeps the browser protocol thin and routes known recon intents to
the bounded recon skill before falling back to the free-form command executor.
"""

from __future__ import annotations

import asyncio
import math
import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from skills.recon_movement import (
    MAX_ANGULAR_SPEED_RADPS,
    ReconMovementSkill,
    SkillResult,
)

BroadcastFn = Callable[[dict], Awaitable[None]]

STOP_COMMANDS = {"stop", "halt", "emergency stop", "e stop", "estop", "hold", "pause"}
AUTONOMY_ENABLE_COMMANDS = {"autonomy on", "enable autonomy", "auto on"}
AUTONOMY_DISABLE_COMMANDS = {"autonomy off", "disable autonomy", "auto off"}

DEFUSAL_BLOCK_PATTERNS = (
    "cut",
    "clip",
    "sever",
    "flip switch",
    "switch",
    "defuse",
    "disarm",
)


@dataclass(frozen=True)
class SkillRoute:
    action: str
    target: str = ""
    distance_m: float = 0.5
    max_duration_s: float = 20.0


@dataclass(frozen=True)
class CommandRoute:
    kind: str
    text: str
    skill: SkillRoute | None = None


def normalize_command(text: str) -> str:
    return " ".join(str(text or "").lower().replace("_", " ").split())


def route_command(text: str) -> CommandRoute:
    command = normalize_command(text)
    if not command:
        return CommandRoute("error", "empty command")
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
    if _is_defusal_manipulation(command):
        return CommandRoute(
            "error",
            "Defusal manipulation is not available; use wire inspection/localization only",
        )
    if _is_scan(command):
        return CommandRoute("skill", "Scanning area", SkillRoute("scan_room"))
    if _is_forward(command):
        return CommandRoute(
            "skill",
            "Moving forward",
            SkillRoute(
                "move_forward",
                distance_m=_extract_distance_m(command),
                max_duration_s=5.0,
            ),
        )
    if _is_approach_threat(command):
        return CommandRoute(
            "skill",
            "Approaching visible threat",
            SkillRoute("approach_detected_threat", max_duration_s=10.0),
        )
    target = _approach_target(command)
    if target:
        return CommandRoute(
            "skill",
            f"Approaching {target}",
            SkillRoute("approach_object", target=target, max_duration_s=10.0),
        )
    return CommandRoute("fallback", "Use free-form command executor")


class MapStreamMobilityAdapter:
    def __init__(self, node: Any, stop_event: threading.Event) -> None:
        self._node = node
        self._stop_event = stop_event

    def rotate(self, angle: float) -> None:
        angle = _clamp(float(angle), -math.pi / 2.0, math.pi / 2.0)
        if abs(angle) <= 1e-3:
            return
        speed = math.copysign(MAX_ANGULAR_SPEED_RADPS, angle)
        self.send_cmd_vel(0.0, speed, abs(angle) / MAX_ANGULAR_SPEED_RADPS)

    def send_cmd_vel(self, linear_x: float, angular_z: float, duration: float) -> None:
        duration = max(0.0, min(float(duration), 2.0))
        deadline = time.time() + duration
        while time.time() < deadline and not self._stop_event.is_set():
            if linear_x > 0 and _blocked_ahead(self._node):
                break
            self._node.publish_twist(linear_x, angular_z)
            time.sleep(0.1)
        self._node.publish_twist(0.0, 0.0)


class ReconCommandRouter:
    def __init__(self, node: Any, broadcast: BroadcastFn) -> None:
        self._node = node
        self._broadcast = broadcast
        self._stop_event = threading.Event()
        self._task: asyncio.Task | None = None

    async def handle(self, text: str) -> bool:
        route = route_command(text)
        if route.kind == "fallback":
            return False
        if route.kind == "error":
            await self._broadcast({"phase": "error", "text": route.text})
            return True
        if route.kind == "stop":
            await self.stop(route.text)
            return True
        if route.kind == "skill" and route.skill is not None:
            await self._start_skill(route)
            return True
        return False

    async def stop(self, message: str = "stop requested") -> None:
        self._stop_event.set()
        try:
            self._node.stop_manual_motion()
        except Exception:
            pass
        try:
            self._node.publish_twist(0.0, 0.0)
        except Exception:
            pass
        await self._broadcast({"phase": "idle", "text": message})

    async def _start_skill(self, route: CommandRoute) -> None:
        if self._task is not None and not self._task.done():
            await self._broadcast(
                {"phase": "error", "text": "busy — wait for current skill to finish"}
            )
            return
        self._stop_event.clear()
        await self._broadcast({"phase": "executing", "text": route.text})
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run_skill(route))

    async def _run_skill(self, route: CommandRoute) -> None:
        assert route.skill is not None
        loop = asyncio.get_running_loop()
        message, status = await loop.run_in_executor(None, self._execute_skill, route.skill)
        if self._stop_event.is_set():
            await self._broadcast({"phase": "idle", "text": "movement cancelled"})
            return
        phase = "done" if status == SkillResult.SUCCESS else "error"
        await self._broadcast({"phase": phase, "text": str(message)})

    def _execute_skill(self, route: SkillRoute):
        skill = ReconMovementSkill(
            analyzer=lambda _image: self._node.get_vlm_result() or {},
            sleeper=self._sleep,
        )
        skill.mobility = MapStreamMobilityAdapter(self._node, self._stop_event)
        skill.image = self._node.get_image_b64()
        return skill.execute(
            route.action,
            target=route.target,
            distance_m=route.distance_m,
            max_duration_s=route.max_duration_s,
        )

    def _sleep(self, duration: float) -> None:
        deadline = time.time() + max(0.0, float(duration))
        while time.time() < deadline and not self._stop_event.is_set():
            time.sleep(min(0.1, deadline - time.time()))


def _is_defusal_manipulation(command: str) -> bool:
    if command in {"red", "blue", "green", "cut red", "cut blue", "cut green"}:
        return True
    return any(pattern in command for pattern in DEFUSAL_BLOCK_PATTERNS)


def _is_scan(command: str) -> bool:
    return any(
        phrase in command
        for phrase in (
            "scan",
            "sweep",
            "look around",
            "survey",
            "inspect area",
            "inspect room",
        )
    )


def _is_forward(command: str) -> bool:
    return command in {"forward", "go forward", "move forward", "ahead", "go ahead"} or (
        "forward" in command and not _is_approach_threat(command)
    )


def _is_approach_threat(command: str) -> bool:
    return any(
        phrase in command
        for phrase in (
            "approach device",
            "approach threat",
            "approach the device",
            "approach the threat",
            "inspect device",
            "inspect the device",
            "inspect threat",
            "go to device",
            "move to device",
        )
    )


def _approach_target(command: str) -> str:
    patterns = (
        r"^(?:approach|inspect|go to|move to|move toward|go toward)\s+(?:the\s+)?(.+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, command)
        if match:
            target = match.group(1).strip()
            if target and target not in {"area", "room"}:
                return target
    return ""


def _extract_distance_m(command: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(m|meter|meters)?\b", command)
    if not match:
        return 0.5
    return _clamp(float(match.group(1)), 0.1, 1.0)


def _blocked_ahead(node: Any) -> bool:
    try:
        min_range = node.get_min_forward_range()
    except Exception:
        return False
    return min_range is not None and min_range < 0.5


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
