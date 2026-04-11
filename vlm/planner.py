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
    BEARING_TOLERANCE: float = 0.08   # ~4.5 deg dead zone
    CLOSE_ENOUGH: float = 0.12        # bbox fills ~12% of frame → stop
    RECON_STEP_RAD: float = math.pi / 4  # 45 deg scan steps
    RECON_STEPS_TOTAL: int = 8        # 8 steps = full 360
    APPROACH_SPEED: float = 0.08      # m/s
    APPROACH_DURATION: float = 1.5    # seconds per drive step
    REACQUIRE_SPEED: float = 0.3      # rad/s spin when threat lost
    ADVANCE_SPEED: float = 0.1        # m/s after full scan
    ADVANCE_DURATION: float = 2.0     # seconds forward after full scan

    def __init__(self):
        self.phase: str = "recon"
        self.recon_steps_done: int = 0

    def next_command(self, vlm_result: dict, odom=None) -> RobotCommand:
        """Return the next motor command based on VLM perception.

        Args:
            vlm_result: Output from analyze_frame() or VLMSession.update().
            odom:       Robot odometry (reserved for future map-space planning).
        """
        # Phase transition: threat detected → approach
        if (
            vlm_result.get("threat_detected")
            or vlm_result.get("mission_phase") == "defuse"
            or vlm_result.get("defusal", {}).get("active")
        ):
            self.phase = "approach"

        if self.phase == "recon":
            return self._recon_step(vlm_result)
        return self._approach_step(vlm_result)

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
        if size_proxy < self.CLOSE_ENOUGH:
            return RobotCommand(
                kind="cmd_vel",
                linear_x=self.APPROACH_SPEED,
                duration=self.APPROACH_DURATION,
                reason=f"Approaching {threat['label']} (size={size_proxy:.3f})",
            )

        # Step 3: close enough — done.
        return RobotCommand(
            kind="done",
            reason=f"At {threat['label']} (size={size_proxy:.3f}), ready for defusal",
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
