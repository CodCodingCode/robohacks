"""Prompt templates for each mission phase.

Each function returns (system_instruction, user_prompt) ready to send to Gemini
alongside a camera frame.
"""

# Shared preamble that keeps every response machine-parseable.
_JSON_PREAMBLE = (
    "You are a tactical reconnaissance AI mounted on a bomb-disposal robot. "
    "Respond ONLY with valid JSON — no markdown fences, no commentary."
)

_BBOX_RULE = (
    "For every notable entity you detect (people, suspicious items, doors, "
    "furniture, threats), include a bounding box. Use the format "
    "[y_min, x_min, y_max, x_max] where each value is an integer 0–1000, "
    "normalized to the image dimensions (0 = top/left edge, 1000 = bottom/right edge)."
)

_SEMANTIC_PLAN_RULE = (
    "The semantic_plan is advisory high-level planning only. It must describe "
    "what an operator or separate planner should consider next; it must NOT be "
    "a direct motor command, velocity command, or low-level motion-control instruction."
)


def recon_prompt() -> tuple[str, str]:
    """Room scanning during the recon phase."""
    system = _JSON_PREAMBLE
    user = (
        "Analyze this camera frame from a bomb-disposal robot scouting a building.\n"
        "\n"
        "Return JSON with this exact schema:\n"
        "{\n"
        '  "rooms": [\n'
        "    {\n"
        '      "type": "<room type, e.g. Kitchen, Hallway, Office, Lobby>",\n'
        '      "people": <int, number of people visible>,\n'
        '      "objects": ["<notable object>", ...],\n'
        '      "threats": ["<description of any suspicious item>", ...]\n'
        "    }\n"
        "  ],\n"
        '  "annotations": [\n'
        "    {\n"
        '      "label": "<what it is, e.g. person, desk, suspicious backpack>",\n'
        '      "bbox": [y_min, x_min, y_max, x_max],\n'
        '      "category": "<person | threat | object>"\n'
        "    }\n"
        "  ],\n"
        '  "threat_detected": <bool, true if ANY item looks like an explosive device>,\n'
        '  "semantic_plan": {\n'
        '    "next_action": "<high-level advisory action, e.g. continue scan, inspect object, hold for operator>",\n'
        '    "rationale": "<short explanation grounded in the visible frame>",\n'
        '    "confidence": "<high | medium | low>"\n'
        "  }\n"
        "}\n"
        "\n"
        "Rules:\n"
        "- List every distinct room area visible in the frame.\n"
        "- A threat is any item resembling an explosive device: exposed wires, timers, "
        "packages with wires, pipe-like objects with attached electronics, etc.\n"
        "- If nothing suspicious is visible, threats should be an empty list and "
        "threat_detected should be false.\n"
        "- People count should only include clearly visible humans.\n"
        f"- {_BBOX_RULE}\n"
        "- Every person and threat MUST have an annotation with a bounding box.\n"
        "- Include annotations for important objects like doors, desks, and windows too.\n"
        f"- {_SEMANTIC_PLAN_RULE}"
    )
    return system, user


def defusal_prompt() -> tuple[str, str]:
    """Wire-level analysis when a threat device is in view (arm camera)."""
    system = _JSON_PREAMBLE
    user = (
        "You are looking at a suspected explosive device through the robot's arm camera.\n"
        "\n"
        "Return JSON with this exact schema:\n"
        "{\n"
        '  "device_description": "<brief description of the device>",\n'
        '  "wires": [\n'
        "    {\n"
        '      "color": "<wire color>",\n'
        '      "connection": "<what the wire connects to: timer | battery | detonator | unknown>",\n'
        '      "risk": "<high | medium | low>"\n'
        "    }\n"
        "  ],\n"
        '  "annotations": [\n'
        "    {\n"
        '      "label": "<what it is, e.g. red wire, timer, battery>",\n'
        '      "bbox": [y_min, x_min, y_max, x_max],\n'
        '      "category": "<wire | device | component>"\n'
        "    }\n"
        "  ],\n"
        '  "recommendation": "<inspection/localization recommendation; do NOT instruct to cut or flip anything>",\n'
        '  "confidence": "<high | medium | low>",\n'
        '  "semantic_plan": {\n'
        '    "next_action": "<high-level advisory action, e.g. improve view, hold for operator, inspect connection>",\n'
        '    "rationale": "<short explanation grounded in the visible wiring>",\n'
        '    "confidence": "<high | medium | low>"\n'
        "  }\n"
        "}\n"
        "\n"
        "Rules:\n"
        "- List every visible wire with its color and where it appears to connect.\n"
        "- Risk is based on how likely cutting that wire would trigger detonation.\n"
        "- Recommendation should describe what to inspect or localize next for an operator or trained policy.\n"
        "- Do NOT recommend cutting wires, flipping switches, or any direct manipulation action.\n"
        "- If you cannot clearly see the wiring, set confidence to low.\n"
        f"- {_BBOX_RULE}\n"
        "- Every wire, the device body, and any visible components (timer, battery, "
        "detonator) MUST have an annotation with a bounding box.\n"
        f"- {_SEMANTIC_PLAN_RULE}"
    )
    return system, user


def operator_qa_prompt(question: str) -> tuple[str, str]:
    """Operator asks a free-form question about the current frame.

    Returns plain text (not JSON) so the operator gets a natural answer.
    """
    system = (
        "You are a tactical reconnaissance AI on a bomb-disposal robot. "
        "Answer the operator's question about the current camera frame. "
        "Be concise and actionable."
    )
    user = f"Operator question: {question}"
    return system, user
