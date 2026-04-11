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

import google.generativeai as genai

from vlm.prompts import recon_prompt, defusal_prompt, operator_qa_prompt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Set via environment variable or replace with your key for testing.
_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini 2.5 Flash — fast and cheap, good enough for structured vision tasks.
_MODEL = "gemini-2.5-flash-preview-04-17"

# Rate limiting: minimum seconds between Gemini calls.
_MIN_INTERVAL = 2.0
_last_call: float = 0.0

# ---------------------------------------------------------------------------
# Client setup
# ---------------------------------------------------------------------------

_client: genai.GenerativeModel | None = None


def _get_client() -> genai.GenerativeModel:
    global _client
    if _client is None:
        api_key = _API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Export it or pass it in the environment."
            )
        genai.configure(api_key=api_key)
        _client = genai.GenerativeModel(_MODEL)
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

    return _parse_response(raw, phase)


def ask_operator_question(image_b64: str, question: str) -> str:
    """Let an operator ask a free-form question about the current frame.

    Returns a plain-text answer string.
    """
    system, user_text = operator_qa_prompt(question)
    return _call_gemini(system, user_text, image_b64)


# ---------------------------------------------------------------------------
# Gemini call
# ---------------------------------------------------------------------------


def _call_gemini(system: str, user_text: str, image_b64: str) -> str:
    """Send a frame + prompt to Gemini and return the raw text response."""
    client = _get_client()

    image_bytes = base64.b64decode(image_b64)
    image_part = {"mime_type": "image/jpeg", "data": image_bytes}

    response = client.generate_content(
        [
            {"role": "user", "parts": [image_part, {"text": user_text}]},
        ],
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=1024,
        ),
        safety_settings={
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        },
    )

    return response.text


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def _parse_json(text: str) -> dict:
    """Extract JSON from Gemini's response, stripping markdown fences if present."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Strip ```json ... ``` fences.
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
        # Unparseable response — return empty so the dashboard keeps running.
        if phase == "defusal":
            return {
                "defusal": {
                    "active": True,
                    "device_description": "VLM parse error — waiting for next frame",
                    "wires": [],
                    "recommendation": "Hold — retrying analysis",
                    "confidence": "low",
                }
            }
        return {"rooms": []}

    if phase == "recon":
        return _format_recon(data)
    return _format_defusal(data)


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

    result: dict = {"rooms": rooms}

    # If a threat was detected, auto-activate defusal mode.
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
        "defusal": {
            "active": True,
            "device_description": data.get("device_description", ""),
            "wires": wires,
            "recommendation": data.get("recommendation", ""),
            "confidence": data.get("confidence", "low"),
        }
    }
