#!/usr/bin/env python3
"""Fetch a Remix pair and prepare the selected line weight in the run cache."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime/src"))

SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SAFE_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
REPOSITORY = "Remix-Design/RemixIcon"
DEFAULT_VERSION = "4.9.0"
TREE_URL = "https://api.github.com/repos/{repository}/git/trees/v{version}?recursive=1"
RAW_URL = "https://raw.githubusercontent.com/{repository}/v{version}/{path}"
LICENSE_URL = "https://github.com/Remix-Design/RemixIcon/blob/v{version}/License"
DEFAULT_LINE_WEIGHT = "fine"
LINE_WEIGHTS = ("fine", "original")


def request(url: str) -> bytes:
    headers = {"User-Agent": "SlidePoise Remix Icon fetcher", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return response.read()


def validate_svg(data: bytes) -> list[float]:
    root = ET.fromstring(data.decode("utf-8"))
    if root.tag.split("}")[-1].lower() != "svg" or not root.attrib.get("viewBox"):
        raise ValueError("file is not a viewBox SVG")
    for element in root.iter():
        local = element.tag.split("}")[-1].lower()
        if local in {"script", "foreignobject"}:
            raise ValueError(f"unsafe SVG element: {local}")
        for key, value in element.attrib.items():
            attr = key.split("}")[-1].lower()
            lowered = str(value).strip().lower()
            if attr.startswith("on") or lowered.startswith(("javascript:", "data:")):
                raise ValueError("active SVG content is not allowed")
    values = [float(value) for value in root.attrib["viewBox"].replace(",", " ").split()]
    if len(values) != 4 or values[2:] != [24.0, 24.0]:
        raise ValueError(f"unexpected Remix Icon viewBox: {root.attrib['viewBox']}")
    return values


def locate_pair(name: str, version: str) -> dict[str, str]:
    url = TREE_URL.format(repository=REPOSITORY, version=version)
    tree = json.loads(request(url).decode("utf-8"))
    if tree.get("truncated"):
        raise ValueError("official repository tree response was truncated")
    result = {}
    for variant in ("line", "fill"):
        suffix = f"/{name}-{variant}.svg"
        matches = [item["path"] for item in tree.get("tree", []) if item.get("type") == "blob" and str(item.get("path", "")).startswith("icons/") and str(item.get("path", "")).endswith(suffix)]
        if len(matches) != 1:
            raise ValueError(f"Expected one official {name}-{variant}.svg, found {len(matches)}")
        result[variant] = matches[0]
    if Path(result["line"]).parent != Path(result["fill"]).parent:
        raise ValueError("line/fill candidates do not share one official Remix Icon category")
    return result


def fetch_pair(name: str, version: str, output_dir: Path, *, line_weight: str = DEFAULT_LINE_WEIGHT) -> dict:
    if not SAFE_NAME.fullmatch(name):
        raise ValueError("Remix Icon name must contain lowercase letters, digits, and hyphens only")
    if not SAFE_VERSION.fullmatch(version):
        raise ValueError("Remix Icon version must use major.minor.patch")
    if line_weight not in LINE_WEIGHTS:
        raise ValueError("Remix line weight must be fine or original")
    paths = locate_pair(name, version)
    output_dir.mkdir(parents=True, exist_ok=True)
    category = Path(paths["line"]).parent.name
    # Fine applies to generic symbols. Preserve exact artwork in the logo category.
    effective_weight = "original" if category.casefold() == "logos" else line_weight
    pair_id = f"remix-{name}"
    asset_ids = [f"{pair_id}-line-fine" if effective_weight == "fine" else f"{pair_id}-line", f"{pair_id}-fill"]
    assets = []
    for variant, repository_path in paths.items():
        url = RAW_URL.format(repository=REPOSITORY, version=version, path=urllib.parse.quote(repository_path, safe="/"))
        data = request(url)
        validate_svg(data)
        original = output_dir / f"{pair_id}-{variant}.svg"
        original.write_bytes(data)
        output = original
        output_data = data
        treatment = {"id": "original", "line_weight": "original" if variant == "line" else None}
        if variant == "line" and effective_weight == "fine":
            try:
                from slidepoise.icon_geometry import fine_remix_svg
            except ImportError as error:
                raise RuntimeError("Fine needs the packaged Shapely and FontTools dependencies. Run slidepoise setup.") from error
            try:
                output_data, treatment = fine_remix_svg(data)
            except ValueError as error:
                raise ValueError(
                    f"Cannot prepare Fine for {name}. Original SVG retained at {original}. "
                    f"Inspect it and explicitly choose --line-weight original or another icon. {error}"
                ) from error
            output = output_dir / f"{pair_id}-line-fine.svg"
            output.write_bytes(output_data)
        asset = {
            "asset_id": asset_ids[0 if variant == "line" else 1],
            "canonical_file": str(output.resolve()),
            "source_asset_id": f"{pair_id}-{variant}",
            "source_file": str(original.resolve()),
            "source_sha256": hashlib.sha256(data).hexdigest(),
            "source_url": url,
            "source_repository_path": repository_path,
            "provider": "Remix Icon",
            "provider_version": version,
            "license": "Remix Icon License v1.0",
            "license_url": LICENSE_URL.format(version=version),
            "attribution_notice": "This project uses icons from Remix Icon (https://remixicon.com), licensed under the Remix Icon License v1.0.",
            "style_variant": variant,
            "style_pair_id": pair_id,
            "pair_asset_ids": asset_ids,
            "intrinsic_aspect_ratio": 1.0,
            "treatment_recolorable": True,
            "recolor_mode": "fill_all",
            "preserve_canonical_color": False,
            "sha256": hashlib.sha256(output_data).hexdigest(),
            "geometry_treatment": treatment,
            "persistence": "run_cache_only",
            "selection_status": "candidate_pending_post_generation_visual_review",
        }
        output.with_suffix(".provenance.json").write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")
        assets.append(asset)
    pair = {
        "pair_id": pair_id,
        "semantic_icon_name": name,
        "provider": "Remix Icon",
        "provider_version": version,
        "category": category,
        "requested_line_weight": line_weight,
        "line_weight": effective_weight,
        "original_geometry_reason": "exact_identity_category" if category.casefold() == "logos" else None,
        "candidates": assets,
        "selection_owner": "host_agent_post_generation_visual_review",
    }
    manifest = output_dir / f"{pair_id}.pair.json"
    manifest.write_text(json.dumps(pair, indent=2) + "\n", encoding="utf-8")
    return {"pair_manifest": str(manifest.resolve()), **pair}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Official Remix Icon base name without -line or -fill")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version")
    parser.add_argument("--line-weight", choices=LINE_WEIGHTS, help="Override the configured weight. Fine is the default.")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source = ((config.get("remote_sources") or {}).get("remix_icon") or {})
    if not source.get("enabled"):
        raise SystemExit("Remix Icon retrieval is disabled in the resolved config")
    try:
        pair = fetch_pair(args.name.strip().lower(), str(args.version or source.get("provider_version") or DEFAULT_VERSION).strip(),
                          args.output_dir, line_weight=args.line_weight or source.get("line_weight", DEFAULT_LINE_WEIGHT))
    except (ValueError, RuntimeError) as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(pair, indent=2))


if __name__ == "__main__":
    main()
