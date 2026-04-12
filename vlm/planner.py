"""VLM-to-Navigation planner bridge — full autonomous bomb-disposal FSM.

Phases (in order):
    scanning           – 360° rotate-scan, advance, repeat
    person_detected    – transient: VLM found a person
    approaching_person – drive toward person using VLM bearing
    evacuating         – stopped near person, TTS plays evacuation warning
    searching          – resume recon scanning for bomb
    bomb_detected      – transient: VLM found a threat
    approaching_bomb   – orient + drive toward bomb
    defusing           – pick lowest-risk wire, publish cut action
    done               – mission complete, stop

Usage in the planner thread (map_stream_node.py):

    planner = MissionPlanner()
    while True:
        cmd = planner.next_command(vlm_result)
        execute(cmd)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable


@dataclass
class RobotCommand:
    """A single motor command for the skill loop to execute.

    kind:
        "rotate"   → self.mobility.rotate(angle)
        "cmd_vel"  → self.mobility.send_cmd_vel(linear_x, angular_z, duration)
        "wait"     → time.sleep(duration)
        "speak"    → play TTS message (text in `reason`)
        "defuse"   → publish wire-cut action (wire color in `reason`)
        "done"     → mission complete
    """

    kind: str
    angle: float = 0.0
    linear_x: float = 0.0
    angular_z: float = 0.0
    duration: float = 0.0
    reason: str = ""


def bbox_to_bearing(
    bbox: list[int],
    fov_rad: float = 1.2,
) -> tuple[float, float]:
    """Convert a bounding box to a bearing angle and distance proxy."""
    x_center = (bbox[1] + bbox[3]) / 2.0
    offset_frac = (x_center - 500.0) / 500.0
    bearing = offset_frac * (fov_rad / 2.0)

    bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    size_proxy = bbox_area / (1000.0 * 1000.0)

    return bearing, size_proxy


class MissionPlanner:
    """Full autonomous bomb-disposal FSM.

    Phase transitions happen automatically based on VLM perception.
    External code only calls next_command() each cycle.
    """

    BEARING_TOLERANCE: float = 0.10
    CLOSE_ENOUGH: float = 0.35
    CLOSE_ENOUGH_M: float = 0.20
    RECON_STEP_RAD: float = math.pi / 4
    RECON_STEPS_TOTAL: int = 8
    APPROACH_SPEED: float = 0.15
    APPROACH_DURATION: float = 2.5
    REACQUIRE_SPEED: float = 0.4
    ADVANCE_SPEED: float = 0.15
    ADVANCE_DURATION: float = 2.0
    EVAC_WAIT_SECONDS: float = 12.0

    def __init__(self):
        self.phase: str = "scanning"
        self.recon_steps_done: int = 0
        self._person_found: bool = False
        self._evac_spoken: bool = False
        self._defuse_wire: str | None = None

    @property
    def mission_phase(self) -> str:
        return self.phase

    def next_command(self, vlm_result: dict) -> RobotCommand:
        """Return the next motor command based on current phase + VLM."""

        if self.phase == "scanning":
            return self._phase_scanning(vlm_result)
        elif self.phase == "person_detected":
            self.phase = "approaching_person"
            return RobotCommand(kind="wait", duration=0.5,
                                reason="Person detected — starting approach")
        elif self.phase == "approaching_person":
            return self._phase_approaching(vlm_result, target_category="person")
        elif self.phase == "evacuating":
            return self._phase_evacuating(vlm_result)
        elif self.phase == "searching":
            return self._phase_searching(vlm_result)
        elif self.phase == "bomb_detected":
            self.phase = "approaching_bomb"
            return RobotCommand(kind="wait", duration=0.5,
                                reason="Bomb detected — starting approach")
        elif self.phase == "approaching_bomb":
            return self._phase_approaching(vlm_result, target_category="threat")
        elif self.phase == "defusing":
            return self._phase_defusing(vlm_result)
        elif self.phase == "done":
            return RobotCommand(kind="done", reason="Mission complete")
        return RobotCommand(kind="wait", duration=1.0, reason=f"Unknown phase: {self.phase}")

    def _phase_scanning(self, vlm_result: dict) -> RobotCommand:
        """Scan environment. Transition to person_detected or bomb_detected."""
        if self._detect_person(vlm_result):
            self.phase = "person_detected"
            return RobotCommand(kind="wait", duration=0.2,
                                reason="Person spotted during scan")

        if self._detect_threat(vlm_result):
            self.phase = "bomb_detected"
            return RobotCommand(kind="wait", duration=0.2,
                                reason="Threat spotted during scan")

        hint = _parse_semantic_hint(
            vlm_result.get("semantic_plan", {}).get("next_action", "")
        )
        rationale = vlm_result.get("semantic_plan", {}).get("rationale", "")
        if hint == "hold":
            return RobotCommand(kind="wait", duration=2.0,
                                reason=f"VLM advisory: hold — {rationale}")
        if hint == "advance":
            self.recon_steps_done = 0
            return RobotCommand(kind="cmd_vel", linear_x=self.ADVANCE_SPEED,
                                duration=self.ADVANCE_DURATION,
                                reason=f"VLM advisory: advance — {rationale}")
        return self._recon_step()

    def _phase_searching(self, vlm_result: dict) -> RobotCommand:
        """Resume scanning after evacuation, looking for bomb."""
        if self._detect_threat(vlm_result):
            self.phase = "bomb_detected"
            return RobotCommand(kind="wait", duration=0.2,
                                reason="Threat spotted while searching")

        hint = _parse_semantic_hint(
            vlm_result.get("semantic_plan", {}).get("next_action", "")
        )
        rationale = vlm_result.get("semantic_plan", {}).get("rationale", "")
        if hint == "hold":
            return RobotCommand(kind="wait", duration=2.0,
                                reason=f"VLM advisory: hold — {rationale}")
        if hint == "advance":
            self.recon_steps_done = 0
            return RobotCommand(kind="cmd_vel", linear_x=self.ADVANCE_SPEED,
                                duration=self.ADVANCE_DURATION,
                                reason=f"VLM advisory: advance — {rationale}")
        return self._recon_step()

    def _phase_approaching(self, vlm_result: dict, target_category: str) -> RobotCommand:
        """Drive toward a target (person or threat). Transition when close."""
        target = self._find_target(vlm_result, target_category)

        if target is None:
            return RobotCommand(kind="cmd_vel", angular_z=self.REACQUIRE_SPEED,
                                duration=1.0,
                                reason=f"Lost {target_category}, spinning to re-acquire")

        bearing, size_proxy = bbox_to_bearing(target["bbox"])

        if abs(bearing) > self.BEARING_TOLERANCE:
            return RobotCommand(kind="rotate", angle=bearing,
                                reason=f"Centering on {target['label']} (bearing={bearing:+.2f})")

        depth_m = vlm_result.get("_threat_depth_m")
        if depth_m is not None:
            close = depth_m < self.CLOSE_ENOUGH_M
            dist_label = f"depth={depth_m:.2f}m"
        else:
            close = size_proxy >= self.CLOSE_ENOUGH
            dist_label = f"size={size_proxy:.3f}"

        if not close:
            return RobotCommand(kind="cmd_vel", linear_x=self.APPROACH_SPEED,
                                duration=self.APPROACH_DURATION,
                                reason=f"Approaching {target['label']} ({dist_label})")

        if target_category == "person":
            self.phase = "evacuating"
            return RobotCommand(kind="wait", duration=0.5,
                                reason=f"At person ({dist_label}), starting evacuation")
        else:
            self.phase = "defusing"
            return RobotCommand(kind="wait", duration=0.5,
                                reason=f"At bomb ({dist_label}), starting defusal")

    def _phase_evacuating(self, vlm_result: dict) -> RobotCommand:
        """Speak evacuation warning, then transition to searching."""
        if not self._evac_spoken:
            self._evac_spoken = True
            return RobotCommand(
                kind="speak",
                duration=self.EVAC_WAIT_SECONDS,
                reason=(
                    "Attention. This is an emergency. A potential explosive device "
                    "has been detected in this area. For your safety, evacuate the "
                    "building immediately. Move away from the area calmly and quickly. "
                    "Do not touch any suspicious objects. Emergency services have been "
                    "contacted. Please proceed to the nearest exit now."
                ),
            )
        self.phase = "searching"
        self.recon_steps_done = 0
        return RobotCommand(kind="wait", duration=0.5,
                            reason="Evacuation warning delivered, resuming search")

    def _phase_defusing(self, vlm_result: dict) -> RobotCommand:
        """Pick lowest-risk wire and send cut command."""
        if self._defuse_wire is not None:
            self.phase = "done"
            return RobotCommand(kind="done",
                                reason=f"Defusal complete — cut {self._defuse_wire} wire")

        defusal = vlm_result.get("defusal", {})
        wires = defusal.get("wires", [])
        if not wires:
            return RobotCommand(kind="wait", duration=2.0,
                                reason="Waiting for VLM wire analysis")

        risk_order = {"low": 0, "medium": 1, "high": 2, "unknown": 1}
        safest = min(wires, key=lambda w: risk_order.get(w.get("risk", "unknown"), 1))
        self._defuse_wire = safest.get("color", "unknown")
        return RobotCommand(kind="defuse",
                            reason=f"cut {self._defuse_wire}",
                            duration=3.0)

    def _recon_step(self) -> RobotCommand:
        if self.recon_steps_done >= self.RECON_STEPS_TOTAL:
            self.recon_steps_done = 0
            return RobotCommand(kind="cmd_vel", linear_x=self.ADVANCE_SPEED,
                                duration=self.ADVANCE_DURATION,
                                reason="Full scan complete, advancing")
        self.recon_steps_done += 1
        return RobotCommand(
            kind="rotate", angle=self.RECON_STEP_RAD,
            reason=f"Recon scan step {self.recon_steps_done}/{self.RECON_STEPS_TOTAL}")

    @staticmethod
    def _detect_person(vlm_result: dict) -> bool:
        people_count = sum(
            r.get("people", 0) for r in vlm_result.get("rooms", [])
        )
        person_anns = [
            a for a in vlm_result.get("annotations", [])
            if a.get("category") == "person"
        ]
        return people_count > 0 or len(person_anns) > 0

    @staticmethod
    def _detect_threat(vlm_result: dict) -> bool:
        if vlm_result.get("threat_detected"):
            return True
        if vlm_result.get("defusal", {}).get("active"):
            return True
        threat_anns = [
            a for a in vlm_result.get("annotations", [])
            if a.get("category") == "threat"
        ]
        return len(threat_anns) > 0

    @staticmethod
    def _find_target(vlm_result: dict, category: str) -> dict | None:
        annotations = vlm_result.get("annotations", [])
        matches = [a for a in annotations if a.get("category") == category]
        if not matches:
            return None
        return max(matches, key=lambda a: _bbox_area(a.get("bbox", [0, 0, 0, 0])))

    @staticmethod
    def _find_priority_target(vlm_result: dict) -> dict | None:
        """Return the highest-priority visible annotation (threat > person)."""
        annotations = vlm_result.get("annotations", [])
        threats = [a for a in annotations if a.get("category") == "threat"]
        if threats:
            return max(threats, key=lambda a: _bbox_area(a.get("bbox", [0, 0, 0, 0])))
        people = [a for a in annotations if a.get("category") == "person"]
        if people:
            return max(people, key=lambda a: _bbox_area(a.get("bbox", [0, 0, 0, 0])))
        return None

    def reset(self):
        self.phase = "scanning"
        self.recon_steps_done = 0
        self._person_found = False
        self._evac_spoken = False
        self._defuse_wire = None


# Keep the old Planner name as an alias for backward compatibility
Planner = MissionPlanner


def _bbox_area(bbox: list[int]) -> int:
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


def _parse_semantic_hint(next_action: str) -> str | None:
    if not next_action:
        return None
    s = next_action.lower()
    if any(w in s for w in ("hold", "wait", "operator", "pause", "stop")):
        return "hold"
    if any(w in s for w in ("advance", "forward", "proceed", "move to")):
        return "advance"
    return None
