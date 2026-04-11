"""Prompt templates for each mission phase.

Each function returns (system_instruction, user_prompt) ready to send to Gemini
alongside a camera frame.
"""

# Shared preamble that keeps every response machine-parseable.
_JSON_PREAMBLE = (
    "You are a tactical reconnaissance AI mounted on a bomb-disposal robot. "
    "Respond ONLY with valid JSON — no markdown fences, no commentary."
)


def recon_prompt() -> tuple[str, str]:
    """Room scanning during the recon phase.

    Expected output shape (list of rooms visible in the frame):
    {
      "rooms": [
        {
          "type":    str,          # e.g. "Kitchen", "Hallway", "Office"
          "people":  int,          # count of visible people
          "objects": [str, ...],   # notable objects
          "threats": [str, ...]    # empty list if none visible
        }
      ],
      "threat_detected": bool      # true → caller should switch to defusal
    }
    """
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
        '  "threat_detected": <bool, true if ANY item looks like an explosive device>\n'
        "}\n"
        "\n"
        "Rules:\n"
        "- List every distinct room area visible in the frame.\n"
        "- A threat is any item resembling an explosive device: exposed wires, timers, "
        "packages with wires, pipe-like objects with attached electronics, etc.\n"
        "- If nothing suspicious is visible, threats should be an empty list and "
        "threat_detected should be false.\n"
        "- People count should only include clearly visible humans."
    )
    return system, user


def defusal_prompt() -> tuple[str, str]:
    """Wire-level analysis when a threat device is in view (arm camera).

    Expected output shape:
    {
      "device_description": str,
      "wires": [
        {
          "color":      str,
          "connection": str,    # e.g. "timer", "battery", "detonator", "unknown"
          "risk":       str     # "high" | "medium" | "low"
        }
      ],
      "recommendation": str,   # e.g. "Cut the blue wire"
      "confidence":     str    # "high" | "medium" | "low"
    }
    """
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
        '  "recommendation": "<which wire to cut and why>",\n'
        '  "confidence": "<high | medium | low>"\n'
        "}\n"
        "\n"
        "Rules:\n"
        "- List every visible wire with its color and where it appears to connect.\n"
        "- Risk is based on how likely cutting that wire would trigger detonation.\n"
        "- Recommendation should be the safest action based on visible connections.\n"
        "- If you cannot clearly see the wiring, set confidence to low."
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
