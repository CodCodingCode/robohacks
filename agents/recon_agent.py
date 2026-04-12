"""Natural-language recon agent for the MARS robot."""

from __future__ import annotations

from typing import List

try:
    from brain_client.agent_types import Agent
except ImportError:  # pragma: no cover - only used for offline imports/tests.
    class Agent:  # type: ignore[no-redef]
        """Minimal fallback so this module can be imported off-robot."""


class ReconAgent(Agent):
    """Agent that routes natural-language recon intent to a bounded skill."""

    @property
    def id(self) -> str:
        return "recon_agent"

    @property
    def display_name(self) -> str:
        return "Recon Agent"

    def get_skills(self) -> List[str]:
        return ["local/recon_movement"]

    def get_inputs(self) -> List[str]:
        return ["micro"]

    def get_prompt(self) -> str:
        return """
You are a cautious reconnaissance robot operator.

Your movement capability is the recon_movement skill. Use it only for
high-level recon movement intents:

- Use action="scan_room" when asked to scan, survey, look around, or inspect
  the current area.
- Use action="move_forward" for a bounded forward move. Pass distance_m when the
  user gives a distance; otherwise use the default.
- Use action="approach_detected_threat" only when the operator asks you to
  approach a visible suspected threat or device.
- Use action="approach_object" with target="<object name>" when the operator
  asks you to move to, approach, inspect, or go toward a specific visible
  object, such as "move to the bag of chips".
- Use action="hold" when the operator says stop, wait, pause, or hold.
- Use action="reset_recon" when asked to resume or reset recon behavior.

Do not invent unsupported controls, arm actions, wire cutting, or direct motor
commands. If the operator asks for something outside recon movement, say that
you can scan, move forward, approach a visible threat, approach a named
visible object, hold, or reset recon.
"""
