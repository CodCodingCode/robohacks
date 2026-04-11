#!/usr/bin/env python3
"""Annotate an image with VLM bounding boxes and save the result.

Runs the VLM on an input image, draws bounding boxes, and saves to vlm/output/.

Usage:
    export GEMINI_API_KEY="your-key"
    python -m vlm.annotate path/to/image.jpg
    python -m vlm.annotate path/to/image.jpg --phase defusal
    python -m vlm.annotate path/to/image.jpg -o custom_output.jpg
"""

import argparse
import base64
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from vlm.analyze import analyze_frame

COLORS = {
    "threat": (255, 68, 68),
    "person": (0, 204, 255),
    "wire": (255, 170, 0),
    "device": (255, 68, 68),
    "component": (255, 170, 0),
    "object": (0, 255, 136),
}
DEFAULT_COLOR = (136, 136, 136)

OUTPUT_DIR = Path(__file__).parent / "output"


def draw_annotations(img: Image.Image, annotations: list) -> Image.Image:
    """Draw bounding boxes and labels on a copy of the image."""
    annotated = img.copy()
    draw = ImageDraw.Draw(annotated)
    w, h = annotated.size

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
    except (OSError, IOError):
        font = ImageFont.load_default()

    for ann in annotations:
        bbox = ann.get("bbox", [])
        if len(bbox) != 4:
            continue

        # Convert 0-1000 normalized to pixel coords
        y0 = int(bbox[0] / 1000 * h)
        x0 = int(bbox[1] / 1000 * w)
        y1 = int(bbox[2] / 1000 * h)
        x1 = int(bbox[3] / 1000 * w)

        category = ann.get("category", "object")
        color = COLORS.get(category, DEFAULT_COLOR)
        label = ann.get("label", "unknown").upper()

        # Draw box
        draw.rectangle([x0, y0, x1, y1], outline=color, width=3)

        # Corner accents
        corner = min(15, (x1 - x0) // 6, (y1 - y0) // 6)
        for cx, cy, dx, dy in [
            (x0, y0, 1, 1), (x1, y0, -1, 1),
            (x0, y1, 1, -1), (x1, y1, -1, -1),
        ]:
            draw.line([(cx, cy), (cx + corner * dx, cy)], fill=color, width=4)
            draw.line([(cx, cy), (cx, cy + corner * dy)], fill=color, width=4)

        # Label with background
        text_bbox = draw.textbbox((0, 0), label, font=font)
        tw = text_bbox[2] - text_bbox[0]
        th = text_bbox[3] - text_bbox[1]
        pad = 4
        lx, ly = x0, y0 - th - pad * 2
        if ly < 0:
            ly = y1 + 2

        draw.rectangle([lx, ly, lx + tw + pad * 2, ly + th + pad * 2], fill=(0, 0, 0, 180))
        draw.text((lx + pad, ly + pad), label, fill=color, font=font)

    return annotated


def main():
    parser = argparse.ArgumentParser(description="Annotate image with VLM bounding boxes")
    parser.add_argument("image", help="Path to input image")
    parser.add_argument("--phase", choices=["recon", "defusal"], default="recon")
    parser.add_argument("-o", "--output", help="Output filename (saved to vlm/output/)")
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"File not found: {img_path}", file=sys.stderr)
        sys.exit(1)

    image_b64 = base64.b64encode(img_path.read_bytes()).decode()
    print(f"Loaded {img_path.name} ({img_path.stat().st_size // 1024} KB)")
    print(f"Phase: {args.phase}")
    print("Calling Gemini...\n")

    result = analyze_frame(image_b64, phase=args.phase)
    annotations = result.get("annotations", [])

    print(f"Got {len(annotations)} annotations:")
    for ann in annotations:
        print(f"  [{ann['category']:>7}] {ann['label']:<30} bbox={ann['bbox']}")

    # Draw and save
    img = Image.open(img_path).convert("RGB")
    annotated = draw_annotations(img, annotations)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_name = args.output or f"{img_path.stem}_annotated.jpg"
    out_path = OUTPUT_DIR / out_name
    annotated.save(out_path, quality=95)

    print(f"\nSaved: {out_path}")

    # Also save the raw JSON
    json_path = OUTPUT_DIR / f"{img_path.stem}_annotations.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved: {json_path}")


if __name__ == "__main__":
    main()
