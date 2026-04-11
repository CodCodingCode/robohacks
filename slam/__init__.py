"""SLAM → dashboard WebSocket bridge.

Exposes the MapStreamSkill, an Innate Skill that reads the robot's
built-in SLAM output (RobotStateType.LAST_MAP + LAST_ODOM) and streams
it as JSON over ws://0.0.0.0:8000/ws in the shape expected by
../dashboard/.

See slam/README.md for the runbook.
"""

from .map_stream_skill import MapStreamSkill

__all__ = ["MapStreamSkill"]
