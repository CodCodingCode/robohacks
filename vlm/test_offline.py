#!/usr/bin/env python3
"""Offline test for the VLM perception module.

Run against any JPEG image — no robot needed.

Usage:
    export GEMINI_API_KEY="your-key-here"
    python -m vlm.test_offline path/to/image.jpg
    python -m vlm.test_offline path/to/image.jpg --phase defusal
    python -m vlm.test_offline path/to/image.jpg --ask "How many exits are visible?"
"""

import argparse
import base64
import json
import sys
from pathlib import Path

from vlm.analyze import analyze_frame, ask_operator_question


def main():
    parser = argparse.ArgumentParser(description="Test VLM perception offline")
    parser.add_argument("image", help="Path to a JPEG image file")
    parser.add_argument(
        "--phase",
        choices=["recon", "defusal"],
        default="recon",
        help="Mission phase (default: recon)",
    )
    parser.add_argument(
        "--ask",
        type=str,
        default=None,
        help="Ask a free-form operator question about the image",
    )
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"File not found: {img_path}", file=sys.stderr)
        sys.exit(1)

    image_b64 = base64.b64encode(img_path.read_bytes()).decode()
    print(f"Loaded {img_path} ({len(image_b64)} bytes b64)\n")

    if args.ask:
        print(f"Q: {args.ask}")
        answer = ask_operator_question(image_b64, args.ask)
        print(f"A: {answer}")
    else:
        print(f"Phase: {args.phase}")
        print("Calling Gemini...\n")
        result = analyze_frame(image_b64, phase=args.phase)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
