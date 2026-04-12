"""Helpers for projecting VLM detections with depth into map coordinates."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

DEFAULT_CAMERA_FOV_RAD = 1.2
MAX_DEPTH_M = 6.5

# Assumed depth per category when no depth image is available.
ASSUMED_DEPTH_M: dict[str, float] = {
    "person": 2.0,
    "threat": 1.5,
    "door": 3.0,
    "object": 2.0,
    "furniture": 1.5,
    "window": 2.5,
}


def assumed_depth_for_category(category: str) -> float:
    """Return a plausible depth (metres) for a detection with no depth image."""
    return ASSUMED_DEPTH_M.get(str(category or "object").lower(), 2.0)


def stable_marker_id(label: str, x: float, y: float, cell_size: float = 0.5) -> str:
    """Stable string ID for an object at world position (x, y).

    Two detections of the same label within *cell_size* metres of each other
    will produce the same ID, enabling cross-frame deduplication.
    """
    gx = round(x / cell_size)
    gy = round(y / cell_size)
    return f"{label}@{gx},{gy}"


def camera_info_to_dict(msg: Any | None) -> dict | None:
    """Return the small CameraInfo subset needed by projection helpers."""
    if msg is None:
        return None
    k = getattr(msg, "k", None)
    if not k or len(k) < 6:
        return None
    return {
        "fx": float(k[0]),
        "cx": float(k[2]),
        "width": int(getattr(msg, "width", 0) or 0),
        "height": int(getattr(msg, "height", 0) or 0),
    }


def decode_depth_image(
    data: bytes,
    width: int,
    height: int,
    encoding: str,
    step: int,
    depth_scale: float = 0.001,
) -> np.ndarray:
    """Decode common ROS depth image encodings into metres."""
    encoding = (encoding or "").lower()
    if encoding in {"16uc1", "mono16"}:
        dtype = np.dtype("<u2")
        scale = depth_scale
    elif encoding == "32fc1":
        dtype = np.dtype("<f4")
        scale = 1.0
    else:
        raise ValueError(f"unsupported depth encoding: {encoding or 'empty'}")

    itemsize = dtype.itemsize
    row_values = step // itemsize if step else width
    raw = np.frombuffer(data, dtype=dtype, count=row_values * height)
    depth = raw.reshape(height, row_values)[:, :width].astype(np.float32)
    depth *= scale
    depth[~np.isfinite(depth)] = np.nan
    depth[depth <= 0.0] = np.nan
    return depth


def sample_depth_at_bbox(
    depth_m: np.ndarray,
    bbox: list[int] | list[float],
    max_depth_m: float = MAX_DEPTH_M,
) -> float | None:
    """Return median depth from the center of a normalized VLM bbox."""
    if not _valid_bbox(bbox) or depth_m.size == 0:
        return None
    height, width = depth_m.shape[:2]
    y0, x0, y1, x1 = _bbox_to_pixels(bbox, width, height)

    box_w = max(1, x1 - x0)
    box_h = max(1, y1 - y0)
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    half_w = max(2, box_w // 10)
    half_h = max(2, box_h // 10)

    sx0 = max(0, cx - half_w)
    sx1 = min(width, cx + half_w + 1)
    sy0 = max(0, cy - half_h)
    sy1 = min(height, cy + half_h + 1)
    sample = depth_m[sy0:sy1, sx0:sx1]
    valid = sample[np.isfinite(sample)]
    valid = valid[(valid > 0.0) & (valid <= max_depth_m)]
    if valid.size == 0:
        return None
    return float(np.median(valid))


def bbox_bearing_rad(
    bbox: list[int] | list[float],
    image_width: int,
    camera_info: dict | None = None,
    fallback_fov_rad: float = DEFAULT_CAMERA_FOV_RAD,
) -> float | None:
    """Estimate horizontal bearing from a normalized VLM bbox."""
    if not _valid_bbox(bbox):
        return None
    x_center_norm = (float(bbox[1]) + float(bbox[3])) / 2.0
    if camera_info and camera_info.get("fx") and camera_info.get("cx") is not None:
        width = int(camera_info.get("width") or image_width or 1000)
        u = (x_center_norm / 1000.0) * max(1, width - 1)
        return math.atan2(u - float(camera_info["cx"]), float(camera_info["fx"]))

    offset_frac = (x_center_norm - 500.0) / 500.0
    return offset_frac * (fallback_fov_rad / 2.0)


def marker_from_annotation(
    annotation: dict,
    depth_m: np.ndarray | None,
    pose: tuple[float, float, float],
    camera_info: dict | None = None,
    marker_id: int | str | None = None,
    now: float | None = None,
) -> dict | None:
    """Project one VLM annotation into a dashboard map marker.

    Falls back to an assumed depth when *depth_m* is None or the depth
    image has no valid pixels at the bbox location, so markers always
    appear on the map regardless of whether a depth camera is connected.
    """
    bbox = annotation.get("bbox")
    category = annotation.get("category", "object")
    label = annotation.get("label", "object")

    # Determine depth and source.
    source = "vlm_depth"
    if depth_m is not None:
        depth = sample_depth_at_bbox(depth_m, bbox)
        image_width = depth_m.shape[1]
    else:
        depth = None
        image_width = int((camera_info or {}).get("width") or 1000)

    if depth is None:
        depth = assumed_depth_for_category(category)
        source = "vlm_assumed"

    bearing = bbox_bearing_rad(bbox, image_width, camera_info)
    if bearing is None:
        return None

    robot_x, robot_y, robot_theta = pose
    world_angle = robot_theta + bearing
    wx = robot_x + depth * math.cos(world_angle)
    wy = robot_y + depth * math.sin(world_angle)

    if marker_id is None:
        marker_id = stable_marker_id(label, wx, wy)

    marker = {
        "id": marker_id,
        "label": label,
        "category": category,
        "x": wx,
        "y": wy,
        "depth_m": depth,
        "bearing_rad": bearing,
        "confidence": float(annotation.get("confidence", 0.7) or 0.7),
        "source": source,
    }
    if now is not None:
        marker["last_seen"] = now
    return marker


def markers_from_annotations(
    annotations: list,
    depth_m: np.ndarray | None,
    pose: tuple[float, float, float] | None,
    camera_info: dict | None = None,
    now: float | None = None,
) -> list[dict]:
    """Project all VLM annotations to world-frame markers.

    Works with *depth_m=None* — falls back to assumed depths per category.
    """
    if pose is None or not isinstance(annotations, list):
        return []
    markers = []
    for annotation in annotations:
        if not isinstance(annotation, dict):
            continue
        marker = marker_from_annotation(
            annotation,
            depth_m,
            pose,
            camera_info=camera_info,
            now=now,
        )
        if marker is not None:
            markers.append(marker)
    return markers


def _bbox_to_pixels(
    bbox: list[int] | list[float],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    y0 = int(max(0, min(height - 1, round(float(bbox[0]) / 1000.0 * height))))
    x0 = int(max(0, min(width - 1, round(float(bbox[1]) / 1000.0 * width))))
    y1 = int(max(y0 + 1, min(height, round(float(bbox[2]) / 1000.0 * height))))
    x1 = int(max(x0 + 1, min(width, round(float(bbox[3]) / 1000.0 * width))))
    return y0, x0, y1, x1


def _valid_bbox(bbox: Any) -> bool:
    return (
        isinstance(bbox, list)
        and len(bbox) == 4
        and all(isinstance(v, (int, float)) for v in bbox)
        and float(bbox[2]) > float(bbox[0])
        and float(bbox[3]) > float(bbox[1])
    )

