import threading

import pytest

from slam.command_executor import CommandExecutor, PlanError, _parse_planner_json


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


def test_build_context_adds_assumed_depth_when_depth_frame_missing():
    node = _DummyNode(
        {
            "annotations": [
                {
                    "label": "backpack",
                    "category": "threat",
                    "bbox": [450, 450, 650, 650],
                }
            ]
        }
    )
    executor = CommandExecutor(node, _noop_broadcast)

    context = executor._build_context()

    annotation = context["annotations"][0]
    assert annotation["depth_m"] == 1.0
    assert annotation["depth_source"] == "assumed_category"
    assert annotation["bearing_rad"] < 0.0


async def _noop_broadcast(_payload):
    return None


class _DummyNode:
    def __init__(self, vlm_result):
        self._lock = threading.Lock()
        self._last_depth_m = None
        self._camera_info = None
        self._vlm_result = vlm_result

    def snapshot(self):
        return None, None, None, None

    def get_vlm_result(self):
        return self._vlm_result
