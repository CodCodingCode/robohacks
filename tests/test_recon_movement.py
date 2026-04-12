import math

from skills.recon_movement import (
    MAX_ANGULAR_SPEED_RADPS,
    MAX_COMMAND_DURATION_S,
    MAX_FORWARD_SPEED_MPS,
    ReconMovementSkill,
    SEARCH_SPIN_SPEED_RADPS,
    SkillResult,
    _bearing_to_angular_z,
)
from vlm.planner import RobotCommand


class FakeMobility:
    def __init__(self):
        self.rotations = []
        self.cmd_vel = []

    def rotate(self, angle):
        self.rotations.append(angle)

    def send_cmd_vel(self, linear_x, angular_z, duration):
        self.cmd_vel.append((linear_x, angular_z, duration))


def make_skill(analyzer=None):
    skill = ReconMovementSkill(analyzer=analyzer, sleeper=lambda _duration: None)
    skill.mobility = FakeMobility()
    return skill


def test_rejects_unknown_action_without_movement():
    skill = make_skill()

    message, status = skill.execute("cut_red_wire")

    assert status == SkillResult.FAILURE
    assert "Unsupported" in message
    assert skill.mobility.rotations == []
    assert skill.mobility.cmd_vel == []


def test_image_bearing_to_angular_z_turns_right_for_right_side_target():
    assert _bearing_to_angular_z(0.3, gain=1.0) < 0.0
    assert _bearing_to_angular_z(-0.3, gain=1.0) > 0.0


def test_scan_room_rotates_in_eight_bounded_steps_then_stops():
    skill = make_skill()

    message, status = skill.execute("scan_room")

    assert status == SkillResult.SUCCESS
    assert message == "Room scan complete"
    assert len(skill.mobility.rotations) == 8
    assert all(math.isclose(angle, math.pi / 4.0) for angle in skill.mobility.rotations)
    assert skill.mobility.cmd_vel[-1] == (0.0, 0.0, 0.1)


def test_move_forward_clamps_distance_and_chunks_velocity_commands():
    skill = make_skill()

    message, status = skill.execute("move_forward", distance_m=99.0, max_duration_s=5.0)

    assert status == SkillResult.SUCCESS
    assert "up to 5.00m" in message
    movement = skill.mobility.cmd_vel[:-1]
    assert len(movement) == 1
    assert all(cmd[0] == MAX_FORWARD_SPEED_MPS for cmd in movement)
    assert all(cmd[1] == 0.0 for cmd in movement)
    assert all(cmd[2] <= MAX_COMMAND_DURATION_S for cmd in movement)
    assert sum(cmd[2] for cmd in movement) == 5.0
    assert skill.mobility.cmd_vel[-1] == (0.0, 0.0, 0.1)


def test_approach_detected_threat_requires_camera_frame():
    skill = make_skill(analyzer=lambda _image: {})

    message, status = skill.execute("approach_detected_threat")

    assert status == SkillResult.FAILURE
    assert "No camera frame" in message
    assert skill.mobility.cmd_vel[-1] == (0.0, 0.0, 0.1)


def test_approach_object_requires_target():
    skill = make_skill(analyzer=lambda _image: {})

    message, status = skill.execute("approach_object")

    assert status == SkillResult.FAILURE
    assert "requires a target" in message
    assert skill.mobility.cmd_vel[-1] == (0.0, 0.0, 0.1)


def test_approach_object_requires_camera_frame():
    skill = make_skill(analyzer=lambda _image: {})

    message, status = skill.execute("approach_object", target="bag of chips")

    assert status == SkillResult.FAILURE
    assert "No camera frame" in message
    assert "bag of chips" in message
    assert skill.mobility.cmd_vel[-1] == (0.0, 0.0, 0.1)


def test_approach_object_rotates_toward_matching_target_annotation():
    def analyzer(_image):
        return {
            "annotations": [
                {"category": "object", "label": "chair", "bbox": [100, 100, 300, 300]},
                {
                    "category": "object",
                    "label": "bag of chips",
                    "bbox": [100, 800, 300, 950],
                },
            ],
        }

    skill = make_skill(analyzer=analyzer)
    skill.image = "fake-b64"

    message, status = skill.execute(
        "approach_object",
        target="chips",
        max_duration_s=1.0,
    )

    assert status == SkillResult.FAILURE
    assert "Could not find or reach" in message
    assert skill.mobility.rotations
    assert skill.mobility.rotations[0] > 0.0
    assert abs(skill.mobility.rotations[0]) <= math.pi / 2.0
    assert skill.mobility.cmd_vel[-1] == (0.0, 0.0, 0.1)


def test_approach_object_moves_toward_centered_matching_target_annotation():
    def analyzer(_image):
        return {
            "annotations": [
                {
                    "category": "object",
                    "label": "bag of chips",
                    "bbox": [450, 450, 550, 550],
                },
            ],
        }

    skill = make_skill(analyzer=analyzer)
    skill.image = "fake-b64"

    message, status = skill.execute(
        "approach_object",
        target="bag of chips",
        max_duration_s=2.0,
    )

    assert status == SkillResult.FAILURE
    assert "Could not find or reach" in message
    movement = skill.mobility.cmd_vel[:-1]
    assert movement
    assert all(0.0 < cmd[0] <= MAX_FORWARD_SPEED_MPS for cmd in movement)
    assert all(cmd[1] == 0.0 for cmd in movement)
    assert all(cmd[2] <= MAX_COMMAND_DURATION_S for cmd in movement)
    assert skill.mobility.cmd_vel[-1] == (0.0, 0.0, 0.1)


def test_approach_object_searches_when_target_is_not_visible():
    def analyzer(_image):
        return {
            "annotations": [
                {"category": "object", "label": "chair", "bbox": [100, 100, 300, 300]},
            ],
        }

    skill = make_skill(analyzer=analyzer)
    skill.image = "fake-b64"

    message, status = skill.execute(
        "approach_object",
        target="bag of chips",
        max_duration_s=1.0,
    )

    assert status == SkillResult.FAILURE
    assert "Could not find or reach" in message
    assert skill.mobility.cmd_vel[0] == (0.0, SEARCH_SPIN_SPEED_RADPS, 1.0)
    assert abs(skill.mobility.cmd_vel[0][1]) <= MAX_ANGULAR_SPEED_RADPS
    assert skill.mobility.cmd_vel[-1] == (0.0, 0.0, 0.1)


def test_approach_detected_threat_finishes_when_planner_reports_done():
    def analyzer(_image):
        return {
            "threat_detected": True,
            "annotations": [
                {"category": "threat", "label": "device", "bbox": [100, 100, 900, 900]}
            ],
        }

    skill = make_skill(analyzer=analyzer)
    skill.image = "fake-b64"

    message, status = skill.execute("approach_detected_threat", max_duration_s=3.0)

    assert status == SkillResult.SUCCESS
    assert "device" in message
    assert skill.mobility.rotations == []
    assert skill.mobility.cmd_vel[-1] == (0.0, 0.0, 0.1)


def test_planner_cmd_vel_is_clamped_before_sending_to_mobility():
    skill = make_skill()

    outcome, budget = skill._run_planner_command(
        RobotCommand(
            kind="cmd_vel",
            linear_x=10.0,
            angular_z=10.0,
            duration=10.0,
            reason="test clamp",
        )
    )

    assert outcome is None
    assert budget == MAX_COMMAND_DURATION_S
    assert skill.mobility.cmd_vel == [
        (MAX_FORWARD_SPEED_MPS, 0.4, MAX_COMMAND_DURATION_S)
    ]
