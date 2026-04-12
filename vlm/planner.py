"""VLM-to-Navigation planner bridge.

Translates VLM perception output (bounding boxes, semantic plan) into
simple motor commands that the Innate skill loop can execute.

The planner never calls ROS2 directly — it outputs a RobotCommand that
maps 1:1 to MobilityInterface methods.

Usage in a skill loop:

    from vlm import VLMSession, Planner

    session = VLMSession()
    planner = Planner()

    while not self._cancelled:
        result = session.update(self.image)
        cmd = planner.next_command(result)

        if cmd.kind == "rotate":
            self.mobility.rotate(cmd.angle)
        elif cmd.kind == "cmd_vel":
            self.mobility.send_cmd_vel(cmd.linear_x, cmd.angular_z, cmd.duration)
        elif cmd.kind == "wait":
            time.sleep(cmd.duration)
        elif cmd.kind == "done":
            break
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------


@dataclass
class RobotCommand:
    """A single motor command for the skill loop to execute.

    kind:
        "rotate"  → self.mobility.rotate(angle)
        "cmd_vel" → self.mobility.send_cmd_vel(linear_x, angular_z, duration)
        "wait"    → time.sleep(duration)
        "done"    → break / transition
    """

    kind: str
    angle: float = 0.0
    linear_x: float = 0.0
    angular_z: float = 0.0
    duration: float = 0.0
    reason: str = ""


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def bbox_to_bearing(
    bbox: list[int],
    fov_rad: float = 1.2,
) -> tuple[float, float]:
    """Convert a bounding box to a bearing angle and distance proxy.

    Args:
        bbox:    [y_min, x_min, y_max, x_max] normalised 0–1000.
        fov_rad: Camera horizontal field of view in radians.
                 Default 1.2 rad (~69 deg) is a reasonable OAK-D estimate.

    Returns:
        (bearing_rad, size_proxy)
        bearing_rad: negative = object is left, positive = right, 0 = centered.
        size_proxy:  0.0 (tiny/far) to 1.0 (fills frame/close).
    """
    x_center = (bbox[1] + bbox[3]) / 2.0
    offset_frac = (x_center - 500.0) / 500.0  # -1 to +1
    bearing = offset_frac * (fov_rad / 2.0)

    bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    size_proxy = bbox_area / (1000.0 * 1000.0)

    return bearing, size_proxy


# ---------------------------------------------------------------------------
# Planner state machine
# ---------------------------------------------------------------------------


class Planner:
    """Reactive planner that converts VLM output to motor commands.

    Two phases:
        RECON   — rotate-scan the room, advance, repeat.
        APPROACH — orient toward threat, drive forward, stop when close.
    """

    # Tunable thresholds — override per-robot via `planner.APPROACH_SPEED = 0.05`
    BEARING_TOLERANCE: float = 0.10   # ~5.7 deg dead zone
    CLOSE_ENOUGH: float = 0.25        # bbox fills ~25% of frame → stop (~1m away)
    CLOSE_ENOUGH_M: float = 0.8       # depth camera: stop when object < 0.8m away
    RECON_STEP_RAD: float = math.pi / 4  # 45 deg scan steps
    RECON_STEPS_TOTAL: int = 8        # 8 steps = full 360
    APPROACH_SPEED: float = 0.15      # m/s
    APPROACH_DURATION: float = 2.5    # seconds per drive step
    REACQUIRE_SPEED: float = 0.4      # rad/s spin when object lost
    ADVANCE_SPEED: float = 0.15       # m/s after full scan
    ADVANCE_DURATION: float = 2.0     # seconds forward after full scan

    def __init__(self):
        self.phase: str = "recon"
        self.recon_steps_done: int = 0

    def next_command(self, vlm_result: dict) -> RobotCommand:
        """Return the next motor command based on VLM perception.

        Args:
            vlm_result: Output from analyze_frame() or VLMSession.update().
                        May include "_threat_depth_m" (float, metres) injected
                        by the planner thread for depth-based termination.
        """
        # Phase transition: threat detected → approach
        if (
            vlm_result.get("threat_detected")
            or vlm_result.get("mission_phase") == "defuse"
            or vlm_result.get("defusal", {}).get("active")
        ):
            self.phase = "approach"

        if self.phase == "recon":
            # Apply semantic hint from Gemini's advisory plan.
            hint = _parse_semantic_hint(
                vlm_result.get("semantic_plan", {}).get("next_action", "")
            )
            rationale = vlm_result.get("semantic_plan", {}).get("rationale", "")
            if hint == "hold":
                return RobotCommand(
                    kind="wait",
                    duration=2.0,
                    reason=f"VLM advisory: hold — {rationale}",
                )
            if hint == "advance":
                # Skip remaining scan steps and move forward now.
                # Reset to 0 (not RECON_STEPS_TOTAL) so the NEXT call to
                # _recon_step doesn't see >= total and advance a second time.
                self.recon_steps_done = 0
                return RobotCommand(
                    kind="cmd_vel",
                    linear_x=self.ADVANCE_SPEED,
                    duration=self.ADVANCE_DURATION,
                    reason=f"VLM advisory: advance — {rationale}",
                )
            return self._recon_step(vlm_result)
        return self._approach_step(vlm_result)

    def preview_command(self, vlm_result: dict) -> RobotCommand:
        """Return what the next command would be WITHOUT mutating any state.

        Safe to call when autonomy is disabled — recon_steps_done and phase
        are never advanced, so the planner stays frozen until execution resumes.
        """
        effective_phase = self.phase
        if (
            vlm_result.get("threat_detected")
            or vlm_result.get("mission_phase") == "defuse"
            or vlm_result.get("defusal", {}).get("active")
        ):
            effective_phase = "approach"

        if effective_phase == "recon":
            # Mirror hint logic from next_command — read-only, no state mutation.
            hint = _parse_semantic_hint(
                vlm_result.get("semantic_plan", {}).get("next_action", "")
            )
            rationale = vlm_result.get("semantic_plan", {}).get("rationale", "")
            if hint == "hold":
                return RobotCommand(kind="wait", duration=2.0,
                                    reason=f"VLM advisory: hold — {rationale}")
            if hint == "advance":
                return RobotCommand(kind="cmd_vel", linear_x=self.ADVANCE_SPEED,
                                    duration=self.ADVANCE_DURATION,
                                    reason=f"VLM advisory: advance — {rationale}")
            return self._preview_recon_step()
        return self._approach_step(vlm_result)  # already non-mutating

    def _preview_recon_step(self) -> RobotCommand:
        """Non-mutating twin of _recon_step — reads counter, never increments."""
        if self.recon_steps_done >= self.RECON_STEPS_TOTAL:
            return RobotCommand(
                kind="cmd_vel",
                linear_x=self.ADVANCE_SPEED,
                duration=self.ADVANCE_DURATION,
                reason="Full scan complete, advancing to next area",
            )
        next_step = self.recon_steps_done + 1  # local only — not stored
        return RobotCommand(
            kind="rotate",
            angle=self.RECON_STEP_RAD,
            reason=f"Recon scan step {next_step}/{self.RECON_STEPS_TOTAL}",
        )

    # -- RECON ---------------------------------------------------------------

    def _recon_step(self, vlm_result: dict) -> RobotCommand:
        if self.recon_steps_done >= self.RECON_STEPS_TOTAL:
            # Full rotation done — advance to next area.
            self.recon_steps_done = 0
            return RobotCommand(
                kind="cmd_vel",
                linear_x=self.ADVANCE_SPEED,
                duration=self.ADVANCE_DURATION,
                reason="Full scan complete, advancing to next area",
            )

        self.recon_steps_done += 1
        return RobotCommand(
            kind="rotate",
            angle=self.RECON_STEP_RAD,
            reason=f"Recon scan step {self.recon_steps_done}/{self.RECON_STEPS_TOTAL}",
        )

    # -- APPROACH ------------------------------------------------------------

    def _approach_step(self, vlm_result: dict) -> RobotCommand:
        threat = self._find_priority_target(vlm_result)

        if threat is None:
            # Lost sight of threat — slow spin to re-acquire.
            return RobotCommand(
                kind="cmd_vel",
                angular_z=self.REACQUIRE_SPEED,
                duration=1.0,
                reason="Threat not in frame, spinning to re-acquire",
            )

        bearing, size_proxy = bbox_to_bearing(threat["bbox"])

        # Step 1: center the threat in the frame.
        if abs(bearing) > self.BEARING_TOLERANCE:
            return RobotCommand(
                kind="rotate",
                angle=bearing,
                reason=f"Centering on {threat['label']} (bearing={bearing:+.2f} rad)",
            )

        # Step 2: drive forward if still far.
        # Prefer depth camera measurement; fall back to bbox size proxy.
        depth_m = vlm_result.get("_threat_depth_m")
        if depth_m is not None:
            close_enough = depth_m < self.CLOSE_ENOUGH_M
            dist_label = f"depth={depth_m:.2f}m"
        else:
            close_enough = size_proxy >= self.CLOSE_ENOUGH
            dist_label = f"size={size_proxy:.3f}"

        if not close_enough:
            return RobotCommand(
                kind="cmd_vel",
                linear_x=self.APPROACH_SPEED,
                duration=self.APPROACH_DURATION,
                reason=f"Approaching {threat['label']} ({dist_label})",
            )

        # Step 3: close enough — done.
        return RobotCommand(
            kind="done",
            reason=f"At {threat['label']} ({dist_label}), ready for defusal",
        )

    # -- Helpers -------------------------------------------------------------

    @staticmethod
    def _find_priority_target(vlm_result: dict) -> dict | None:
        """Find the highest-priority target annotation.

        Prefers threats over people. Among same category, picks largest bbox
        (closest to robot).
        """
        annotations = vlm_result.get("annotations", [])
        threats = [a for a in annotations if a.get("category") == "threat"]
        if threats:
            return max(threats, key=lambda a: _bbox_area(a["bbox"]))

        people = [a for a in annotations if a.get("category") == "person"]
        if people:
            return max(people, key=lambda a: _bbox_area(a["bbox"]))

        return None

    def reset(self):
        """Reset to recon mode."""
        self.phase = "recon"
        self.recon_steps_done = 0


def _bbox_area(bbox: list[int]) -> int:
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


def _parse_semantic_hint(next_action: str) -> str | None:
    """Map a VLM semantic_plan.next_action string to a planner hint token.

    Returns one of: "hold", "advance", None.
    Matching is case-insensitive substring — intentionally loose so varied
    Gemini phrasings all resolve to the same action.
    """
    if not next_action:
        return None
    s = next_action.lower()
    if any(w in s for w in ("hold", "wait", "operator", "pause", "stop")):
        return "hold"
    if any(w in s for w in ("advance", "forward", "proceed", "move to")):
        return "advance"
    return None
