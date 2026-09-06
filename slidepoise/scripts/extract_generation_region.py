#!/usr/bin/env python3
"""Extract the configured substantive generation region from a full-slide render.

This script performs deterministic geometry only. It does not judge whether the render
is visually faithful. Use the resulting crop for target-vs-reconstruction visual review,
then inspect the full render separately for Slide Master frame quality.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    full_w, full_h = map(int, cfg["design"]["full_slide_px"])
    region_w, region_h = map(int, cfg["derived"]["generation_region_px"])
    offset_y = int(cfg["derived"]["generation_offset_y_px"])

    image = Image.open(args.render).convert("RGB")
    scale_x = image.width / full_w
    scale_y = image.height / full_h
    left = 0
    top = round(offset_y * scale_y)
    right = image.width
    bottom = round((offset_y + region_h) * scale_y)
    if bottom <= top or top < 0 or bottom > image.height:
        raise SystemExit("resolved generation region is invalid for this render")

    crop = image.crop((left, top, right, bottom))
    # Normalize to the exact generation-region pixel contract for direct comparison.
    crop = crop.resize((region_w, region_h), Image.Resampling.LANCZOS)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    crop.save(args.output)
    print(json.dumps({
        "render": str(args.render.resolve()),
        "full_slide_px": [full_w, full_h],
        "generation_region_px": [region_w, region_h],
        "generation_offset_y_px": offset_y,
        "render_crop_px": [left, top, right - left, bottom - top],
        "output": str(args.output.resolve()),
        "note": "Geometry extraction only; visual acceptance belongs to the host Agent."
    }, indent=2))


if __name__ == "__main__":
    main()
