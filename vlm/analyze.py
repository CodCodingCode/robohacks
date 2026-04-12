"""VLM perception module — call Gemini with robot camera frames.

Usage from an Innate Skill:

    from vlm.analyze import analyze_frame

    result = analyze_frame(image_b64, phase="recon")
    payload.update(result)          # merges straight into dashboard state

Usage standalone (testing):

    import base64, pathlib
    img_b64 = base64.b64encode(pathlib.Path("test.jpg").read_bytes()).decode()
    result = analyze_frame(img_b64, phase="recon")
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Literal

from google import genai
from google.genai import types

from vlm.prompts import recon_prompt, defusal_prompt, navigation_prompt, operator_qa_prompt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_MODEL = "gemini-2.5-flash"

# Rate limiting: minimum seconds between Gemini calls.
_MIN_INTERVAL = 1.0
_last_call: float = 0.0

# ---------------------------------------------------------------------------
# Client setup
# ---------------------------------------------------------------------------

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Export it or pass it in the environment."
            )
        _client = genai.Client(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------


def analyze_frame(
    image_b64: str,
    phase: Literal["recon", "defusal"] = "recon",
) -> dict:
    """Analyze a single camera frame and return dashboard-ready state.

    Args:
        image_b64: Base64-encoded JPEG from the robot camera.
        phase:     "recon" for room scanning, "defusal" for wire analysis.

    Returns:
        Dict matching the dashboard state contract — can be merged directly
        into the WebSocket payload via ``payload.update(result)``.
    """
    global _last_call

    # Rate limit to avoid hammering the API.
    elapsed = time.time() - _last_call
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)

    if phase == "defusal":
        system, user_text = defusal_prompt()
    else:
        system, user_text = recon_prompt()

    raw = _call_gemini(system, user_text, image_b64)
    _last_call = time.time()

    if os.environ.get("VLM_DEBUG"):
        print(f"[VLM_DEBUG] Raw Gemini response:\n{raw}\n")

    return _parse_response(raw, phase)


def analyze_navigation(image_b64: str) -> dict:
    """Analyze a frame for VLM-guided navigation (obstacle avoidance + path finding).

    Returns a dict with navigation action, obstacles, and person/threat flags.
    """
    global _last_call

    elapsed = time.time() - _last_call
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)

    system, user_text = navigation_prompt()
    raw = _call_gemini(system, user_text, image_b64)
    _last_call = time.time()

    try:
        data = _parse_json(raw)
    except (json.JSONDecodeError, ValueError):
        return {
            "path_clear": True,
            "obstacles": [],
            "person_visible": False,
            "threat_visible": False,
            "annotations": [],
            "navigation": {
                "action": "hold",
                "confidence": "low",
                "rationale": "VLM parse error — waiting for next frame",
            },
        }

    data["annotations"] = _normalize_annotations(data.get("annotations", []))
    nav = data.get("navigation", {})
    if not isinstance(nav, dict):
        nav = {"action": "hold", "confidence": "low", "rationale": ""}
    data["navigation"] = nav
    return data


def ask_operator_question(image_b64: str, question: str) -> str:
    """Let an operator ask a free-form question about the current frame.

    Returns a plain-text answer string.
    """
    system, user_text = operator_qa_prompt(question)
    return _call_gemini(system, user_text, image_b64)


# ---------------------------------------------------------------------------
# Stateful session for the autonomy loop
# ---------------------------------------------------------------------------


class VLMSession:
    """Wraps analyze_frame() with cross-frame state tracking.

    Tracks cumulative rooms and person detections. Phase switching is controlled
    externally, so VLM results never trigger a defusal phase change directly.

    Usage in a skill:

        session = VLMSession()
        while running:
            result = session.update(self.image)
            payload.update(result)
            broadcast(payload)
    """

    def __init__(self):
        self.phase: str = "recon"
        self.rooms_seen: dict[str, dict] = {}
        self.frame_count: int = 0

    def update(self, image_b64: str) -> dict:
        """Analyze a frame using the current phase, update internal state.

        Phase switching is controlled externally (by the planner thread via
        MapStreamNode.set_planner_phase) — this method never auto-switches.
        Returns the full dashboard-ready state dict.
        """
        result = analyze_frame(image_b64, phase=self.phase)
        self.frame_count += 1

        # Accumulate rooms across frames.
        for room in result.get("rooms", []):
            key = room.get("type", "Unknown")
            self.rooms_seen[key] = room

        # Never auto-switch phase — operator controls mode manually.
        # Strip any phase/defusal changes the VLM tries to make.
        result.pop("defusal", None)
        result.pop("mission_phase", None)

        people_count = sum(
            r.get("people", 0) for r in result.get("rooms", [])
        )
        person_annotations = [
            a for a in result.get("annotations", [])
            if a.get("category") == "person"
        ]
        result["evacuation_alert"] = people_count > 0 or len(person_annotations) > 0
        result["people_detected"] = max(people_count, len(person_annotations))

        # Include cumulative rooms (all rooms seen so far, not just this frame).
        result["rooms_cumulative"] = list(self.rooms_seen.values())

        return result

    def reset(self):
        """Reset to recon mode (e.g. after threat is cleared)."""
        self.phase = "recon"
        self.rooms_seen.clear()
        self.frame_count = 0


# ---------------------------------------------------------------------------
# Gemini call
# ---------------------------------------------------------------------------


def _call_gemini(system: str, user_text: str, image_b64: str) -> str:
    """Send a frame + prompt to Gemini and return the raw text response."""
    client = _get_client()

    image_bytes = base64.b64decode(image_b64)
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    text_part = types.Part.from_text(text=user_text)

    response = client.models.generate_content(
        model=_MODEL,
        contents=[image_part, text_part],
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2,
            max_output_tokens=4096,
        ),
    )

    return response.text


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def _parse_json(text: str) -> dict:
    """Extract JSON from Gemini's response, stripping markdown fences if present."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def _parse_response(raw: str, phase: str) -> dict:
    """Parse raw Gemini text into the dashboard state contract.

    Always returns a valid dict — falls back to safe defaults on parse errors
    so the stream never breaks.
    """
    try:
        data = _parse_json(raw)
    except (json.JSONDecodeError, ValueError):
        if phase == "defusal":
            return {
                "semantic_plan": _default_semantic_plan(
                    "hold for operator review",
                    "VLM response could not be parsed; wait for the next frame.",
                ),
                "defusal": {
                    "active": True,
                    "device_description": "VLM parse error — waiting for next frame",
                    "wires": [],
                    "recommendation": "Hold — retrying analysis",
                    "confidence": "low",
                }
            }
        return {
            "rooms": [],
            "annotations": [],
            "semantic_plan": _default_semantic_plan(
                "continue scanning",
                "VLM response could not be parsed; wait for the next frame.",
            ),
        }

    if phase == "recon":
        return _format_recon(data)
    return _format_defusal(data)


def _normalize_annotations(raw_annotations: list) -> list:
    """Validate and normalize bounding box annotations from Gemini."""
    out = []
    for a in raw_annotations:
        bbox = a.get("bbox", [])
        if len(bbox) != 4:
            continue
        bbox = [max(0, min(1000, int(v))) for v in bbox]
        category = a.get("category", "object")
        label = a.get("label", "unknown")
        ann = {
            "label": label,
            "bbox": bbox,
            "category": category,
        }
        if "spatial_layer" in a:
            ann["spatial_layer"] = a["spatial_layer"]
        if "occluded" in a:
            ann["occluded"] = bool(a["occluded"])
        out.append(ann)
    return out


def _default_semantic_plan(next_action: str, rationale: str) -> dict:
    return {
        "next_action": next_action,
        "rationale": rationale,
        "confidence": "low",
    }


def _normalize_semantic_plan(
    raw_plan: object,
    fallback_action: str,
    fallback_rationale: str,
) -> dict:
    """Normalize Gemini's high-level advisory plan.

    The result is intentionally semantic only; robot-control loops must treat
    this as display/planner context, not as a velocity or motion command.
    """
    if not isinstance(raw_plan, dict):
        return _default_semantic_plan(fallback_action, fallback_rationale)

    next_action = str(raw_plan.get("next_action") or fallback_action).strip()
    rationale = str(raw_plan.get("rationale") or fallback_rationale).strip()
    confidence = str(raw_plan.get("confidence") or "low").strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    return {
        "next_action": next_action or fallback_action,
        "rationale": rationale or fallback_rationale,
        "confidence": confidence,
    }


def _format_recon(data: dict) -> dict:
    """Normalize recon response into dashboard state."""
    rooms = []
    for r in data.get("rooms", []):
        rooms.append({
            "type": r.get("type", "Unknown"),
            "people": int(r.get("people", 0)),
            "objects": r.get("objects", []),
            "threats": r.get("threats", []),
        })

    result: dict = {
        "rooms": rooms,
        "annotations": _normalize_annotations(data.get("annotations", [])),
        "semantic_plan": _normalize_semantic_plan(
            data.get("semantic_plan"),
            "continue scanning",
            "No high-level VLM plan was returned for this frame.",
        ),
    }

    if data.get("threat_detected", False):
        threat_descriptions = []
        for r in rooms:
            threat_descriptions.extend(r.get("threats", []))
        result["defusal"] = {
            "active": True,
            "device_description": "; ".join(threat_descriptions) or "Threat detected",
            "wires": [],
            "recommendation": "Move arm camera closer for wire analysis",
            "confidence": "low",
        }
        result["mission_phase"] = "defuse"

    return result


def _format_defusal(data: dict) -> dict:
    """Normalize defusal response into dashboard state."""
    wires = []
    for w in data.get("wires", []):
        wires.append({
            "color": w.get("color", "unknown"),
            "connection": w.get("connection", "unknown"),
            "risk": w.get("risk", "unknown"),
        })

    return {
        "annotations": _normalize_annotations(data.get("annotations", [])),
        "semantic_plan": _normalize_semantic_plan(
            data.get("semantic_plan"),
            "hold for operator review",
            "No high-level VLM plan was returned for this defusal frame.",
        ),
        "defusal": {
            "active": True,
            "device_description": data.get("device_description", ""),
            "wires": wires,
            "recommendation": data.get("recommendation", ""),
            "confidence": data.get("confidence", "low"),
        }
    }
