"""Person detection bridge — extracts person detections from VLM output.

Wraps the existing VLM module (vlm.analyze) and provides a clean
interface for the intruder alert pipeline.  No separate CV model is
needed: Gemini already returns bounding-box annotations with
category="person" during recon analysis.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class PersonDetection:
    """A single detected person in a camera frame."""

    label: str
    bbox: list[int]
    bbox_area: float
    timestamp: float = field(default_factory=time.time)

    @property
    def size_proxy(self) -> float:
        """0.0 (tiny/far) to 1.0 (fills frame/close)."""
        return self.bbox_area / (1000.0 * 1000.0)

    @property
    def is_close(self) -> bool:
        """True when the person occupies >5 % of the frame."""
        return self.size_proxy > 0.05


class PersonDetector:
    """Stateful person detector with cooldown logic.

    Wraps VLM output parsing and tracks when the last alert was issued
    so callers can throttle warnings.
    """

    def __init__(self, cooldown_seconds: float = 15.0):
        self.cooldown = cooldown_seconds
        self._last_alert_time: float = 0.0

    def extract_people(self, vlm_result: dict) -> list[PersonDetection]:
        """Pull person annotations out of a VLM result dict.

        Also counts per-room ``people`` fields as a secondary signal.
        """
        detections: list[PersonDetection] = []
        now = time.time()

        for ann in vlm_result.get("annotations", []):
            if ann.get("category") != "person":
                continue
            bbox = ann.get("bbox", [])
            if len(bbox) != 4:
                continue
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            detections.append(
                PersonDetection(
                    label=ann.get("label", "person"),
                    bbox=bbox,
                    bbox_area=float(area),
                    timestamp=now,
                )
            )

        # Fallback: if no annotations but rooms report people, create a
        # synthetic detection so the alert still fires.
        if not detections:
            total_people = sum(
                r.get("people", 0) for r in vlm_result.get("rooms", [])
            )
            if total_people > 0:
                detections.append(
                    PersonDetection(
                        label=f"{total_people} person(s) reported by VLM",
                        bbox=[0, 0, 500, 500],
                        bbox_area=250000.0,
                        timestamp=now,
                    )
                )

        return detections

    def should_alert(self) -> bool:
        """True if enough time has passed since the last alert."""
        return (time.time() - self._last_alert_time) >= self.cooldown

    def mark_alerted(self) -> None:
        self._last_alert_time = time.time()
