import math

import numpy as np

from slam.depth_fusion import (
    bbox_bearing_rad,
    decode_depth_image,
    marker_from_annotation,
    sample_depth_at_bbox,
)


def test_decode_16uc1_depth_image_to_metres():
    raw = np.array([[1000, 2000], [0, 6500]], dtype=np.uint16).tobytes()

    depth = decode_depth_image(raw, width=2, height=2, encoding="16UC1", step=4)

    assert depth.shape == (2, 2)
    assert depth[0, 0] == 1.0
    assert depth[0, 1] == 2.0
    assert math.isnan(depth[1, 0])
    assert math.isclose(depth[1, 1], 6.5, abs_tol=1e-6)


def test_sample_depth_rejects_invalid_depth():
    depth = np.full((20, 20), np.nan, dtype=np.float32)

    assert sample_depth_at_bbox(depth, [400, 400, 600, 600]) is None


def test_bbox_bearing_uses_camera_info_when_available():
    bearing = bbox_bearing_rad(
        [0, 750, 1000, 850],
        image_width=640,
        camera_info={"fx": 320.0, "cx": 320.0, "width": 640},
    )

    assert bearing is not None
    assert bearing > 0.0


def test_marker_from_annotation_projects_depth_into_map_frame():
    depth = np.full((100, 100), 2.0, dtype=np.float32)
    annotation = {
        "label": "bag of chips",
        "category": "object",
        "bbox": [450, 450, 550, 550],
    }

    marker = marker_from_annotation(annotation, depth, pose=(1.0, 2.0, 0.0), now=10.0)

    assert marker is not None
    assert marker["label"] == "bag of chips"
    assert marker["source"] == "vlm_depth"
    assert marker["depth_m"] == 2.0
    assert marker["x"] == 3.0
    assert marker["y"] == 2.0
    assert marker["last_seen"] == 10.0
