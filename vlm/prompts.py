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

_STANDOFF_RULE = (
    "Proximity rule: the robot must maintain a minimum standoff distance of 15 cm from "
    "any threat or target. If a threat or target appears to occupy more than ~60% of the "
    "frame height (i.e. the robot is within ~15 cm), set proximity_warning to true and "
    "advise halting immediately in the semantic_plan."
)


def recon_prompt() -> tuple[str, str]:
    """Room scanning during the recon phase."""
    system = _JSON_PREAMBLE
    user = (
        "Analyze this camera frame from a bomb-disposal robot scouting a building.\n"
        "\n"
        "Return JSON with this exact schema:\n"
        "{\n"
        '  "reasoning": "<one sentence: what suspicious items, if any, are visible and why>",\n'
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
        '      "category": "<person | threat | object>",\n'
        '      "spatial_layer": "<foreground | midground | background>",\n'
        '      "occluded": <bool, true if the object is partially hidden behind another object>\n'
        "    }\n"
        "  ],\n"
        '  "threat_detected": <bool, true if ANY item looks like an explosive device>,\n'
        '  "traversal_threat_alert": {\n'
        '    "active": <bool, true if a threat is visible while the robot is traversing>,\n'
        '    "description": "<brief description of the detected threat, or empty string if none>"\n'
        "  },\n"
        '  "proximity_warning": <bool, true if any threat or target is within ~15 cm (fills >60% of frame height)>,\n'
        '  "semantic_plan": {\n'
        '    "next_action": "<high-level advisory action, e.g. continue scan, inspect object, halt — proximity limit reached, hold for operator>",\n'
        '    "rationale": "<short explanation grounded in the visible frame>",\n'
        '    "confidence": "<high | medium | low>"\n'
        "  }\n"
        "}\n"
        "\n"
        "Rules:\n"
        "- List every distinct room area visible in the frame.\n"
        "- A threat matches TWO OR MORE of these visual features: "
        "(1) a cardboard or plain box of any size, "
        "(2) colored wires running along its surface, "
        "(3) a green rectangular circuit board (breadboard) sitting on top, "
        "(4) loose electronic components (battery, timer, LED) attached to it. "
        "The primary target device is a brown cardboard box approximately shoebox-sized "
        "with a breadboard and wires on its exterior top surface — classify this as a bomb. "
        "Also flag exposed wires, timers, packages with wires, or pipe-like objects with electronics.\n"
        "- If a cardboard box is visible but you cannot clearly see its top surface "
        "(partial view, distance, occlusion), set threat_detected=true and confidence=low "
        "rather than leaving it undetected. A missed threat is far more dangerous than a false alarm.\n"
        "- If threat_detected=true, there MUST be at least one annotation with "
        'category="threat". If you cannot draw a precise bbox, estimate the region '
        "where the suspicious object appears — do not leave threat_detected=true without an annotation.\n"
        "- If nothing suspicious is visible, threats should be an empty list and "
        "threat_detected should be false.\n"
        "- Set traversal_threat_alert.active to true whenever a threat is visible, regardless "
        "of mission phase; always populate description when active.\n"
        "- People count should only include clearly visible humans.\n"
        f"- {_BBOX_RULE}\n"
        "- Every person and threat MUST have an annotation with a bounding box.\n"
        "- Include annotations for important objects like doors, desks, and windows too.\n"
        "- Detect ALL instances of each object type. If multiple similar objects are "
        "visible (e.g. two cardboard boxes), annotate EACH one separately with its own "
        "bounding box, even if one is partially hidden behind another.\n"
        "- For partially occluded objects, draw the bounding box around the visible "
        "portion and set occluded=true. Use visual cues (relative size, position, "
        "perspective) to assign spatial_layer: objects appearing smaller and higher in "
        "frame are typically farther away (background).\n"
        f"- {_STANDOFF_RULE}\n"
        f"- {_SEMANTIC_PLAN_RULE}"
    )
    return system, user


def defusal_prompt() -> tuple[str, str]:
    """Wire-level analysis when a threat device is in view (arm camera)."""
    system = _JSON_PREAMBLE
    user = (
        "You are looking at a suspected explosive device (a brown cardboard box approximately "
        "shoebox-sized, with a breadboard and wires on its exterior top surface — classify this as a bomb) "
        "through the robot's arm camera.\n"
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
        '  "proximity_warning": <bool, true if the device fills >60% of frame height, indicating the robot is within ~15 cm>,\n'
        '  "semantic_plan": {\n'
        '    "next_action": "<high-level advisory action, e.g. improve view, hold for operator, inspect connection, halt — proximity limit reached>",\n'
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
        f"- {_STANDOFF_RULE}\n"
        f"- {_SEMANTIC_PLAN_RULE}"
    )
    return system, user


def navigation_prompt() -> tuple[str, str]:
    """VLM-guided navigation — obstacle avoidance and path finding."""
    system = _JSON_PREAMBLE
    user = (
        "Analyze this camera frame from a bomb-disposal robot navigating an indoor environment.\n"
        "\n"
        "Return JSON with this exact schema:\n"
        "{\n"
        '  "reasoning": "<one sentence describing visible path and obstacles>",\n'
        '  "path_clear": <bool, true if there is a clear path ahead>,\n'
        '  "obstacles": [\n'
        "    {\n"
        '      "label": "<what it is, e.g. wall, chair, door>",\n'
        '      "bbox": [y_min, x_min, y_max, x_max],\n'
        '      "position": "<left | center | right>"\n'
        "    }\n"
        "  ],\n"
        '  "person_visible": <bool>,\n'
        '  "threat_visible": <bool>,\n'
        '  "annotations": [\n'
        "    {\n"
        '      "label": "<entity description>",\n'
        '      "bbox": [y_min, x_min, y_max, x_max],\n'
        '      "category": "<person | threat | object | obstacle>"\n'
        "    }\n"
        "  ],\n"
        '  "navigation": {\n'
        '    "action": "<advance | turn_left | turn_right | reverse | hold>",\n'
        '    "confidence": "<high | medium | low>",\n'
        '    "rationale": "<why this action is recommended>"\n'
        "  }\n"
        "}\n"
        "\n"
        "Rules:\n"
        "- Focus on navigable space and immediate obstacles.\n"
        "- If a wall blocks the path, recommend turning in the direction with more open space.\n"
        "- If a person is visible, set person_visible=true and include an annotation.\n"
        "- If a suspicious item is visible, set threat_visible=true and include an annotation.\n"
        f"- {_BBOX_RULE}\n"
        f"- {_STANDOFF_RULE}\n"
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
