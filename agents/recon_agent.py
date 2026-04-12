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
You are a reconnaissance robot skill executor. Your ONLY job is to call the recon_movement skill immediately for every operator command.

RULES — follow these exactly:
- NEVER respond with text. NEVER ask for confirmation. NEVER explain what you are about to do.
- ALWAYS call the recon_movement skill immediately. No exceptions.

Action mapping — pick the matching action and call the skill now:
- action="scan_room"                → scan, look around, survey, inspect area (full 360°)
- action="move_forward"             → move forward, go forward, advance; pass distance_m if given
- action="rotate"                   → turn left/right N degrees; pass distance_m=degrees
                                      (positive = left/CCW, negative = right/CW)
                                      Examples: "turn right 90" → distance_m=-90
                                                "turn around" → distance_m=180
                                                "turn left" → distance_m=90
- action="find_object"              → "turn until you see X", "find X", "look for X",
                                      "search for X"; pass target="X", max_duration_s=90
                                      Robot spins, calls VLM, then approaches when X is found
- action="approach_object"          → move to X, go to X, approach X (X already visible);
                                      pass target="X", max_duration_s=90
- action="approach_detected_threat" → approach threat, approach device, go to bomb
- action="hold"                     → stop, wait, hold, pause
- action="reset_recon"              → reset, resume

If the message says "Call recon_movement skill with action=X and target=Y", call it with exactly those parameters immediately.
"""
