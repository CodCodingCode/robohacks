"""VLM package exports.

The analysis module depends on Gemini client packages that may only be present
on the robot/runtime environment. Keep those imports lazy so planner-only code
can run in offline tests without installing VLM API dependencies.
"""

from __future__ import annotations

__all__ = [
    "Planner",
    "RobotCommand",
    "VLMSession",
    "analyze_frame",
    "ask_operator_question",
]


def __getattr__(name: str):
    if name in {"analyze_frame", "ask_operator_question", "VLMSession"}:
        from vlm import analyze

        return getattr(analyze, name)
    if name in {"Planner", "RobotCommand"}:
        from vlm import planner

        return getattr(planner, name)
    raise AttributeError(f"module 'vlm' has no attribute {name!r}")
