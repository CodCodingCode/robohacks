import pytest

from slam.command_executor import PlanError, _parse_planner_json


def test_parse_planner_json_strips_markdown_fence():
    data = _parse_planner_json(
        '```json\n{"steps":[{"op":"stop"}],"rationale":"done"}\n```'
    )

    assert data == {"steps": [{"op": "stop"}], "rationale": "done"}


def test_parse_planner_json_salvages_steps_when_rationale_is_truncated():
    data = _parse_planner_json(
        '{"steps":[{"op":"forward","meters":0.5}],"rationale":"walking toward'
    )

    assert data["steps"] == [{"op": "forward", "meters": 0.5}]
    assert "truncated" in data["rationale"]


def test_parse_planner_json_rejects_unusable_json():
    with pytest.raises(PlanError):
        _parse_planner_json('{"rationale":"missing steps"')
