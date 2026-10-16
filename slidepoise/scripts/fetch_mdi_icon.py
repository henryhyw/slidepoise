#!/usr/bin/env python3
"""Retrieve pinned MDI artwork and retain its original and treatment provenance."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import tarfile
import urllib.request
from pathlib import Path

from fetch_remix_icon_pair import validate_svg

VERSION = "1.2.3"
PACKAGE_URL = f"https://registry.npmjs.org/@iconify-json/mdi/-/mdi-{VERSION}.tgz"
INTEGRITY = "sha512-O3cLwbDOK7NNDf2ihaQOH5F9JglnulNDFV7WprU2dSoZu3h3cWH//h74uQAB87brHmvFVxIOkuBX2sZSzYhScg=="
SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_package(directory: Path) -> tuple[dict, dict, dict]:
    directory.mkdir(parents=True, exist_ok=True)
    cache = directory / f"mdi-{VERSION}.tgz"
    if cache.is_file():
        data = cache.read_bytes()
    else:
        request = urllib.request.Request(PACKAGE_URL, headers={"User-Agent": "SlidePoise MDI fetcher"})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(10_000_001)
    if len(data) > 10_000_000 or "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode() != INTEGRITY:
        raise ValueError("MDI package does not match the pinned release checksum")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        files = []
        for name in ("icons.json", "info.json", "metadata.json"):
            member = archive.getmember("package/" + name)
            if not member.isfile() or member.size > 10_000_000:
                raise ValueError("Unexpected MDI package member")
            files.append(json.loads(archive.extractfile(member).read()))
    cache.write_bytes(data)
    return tuple(files)


def resolve_icon(name: str, icons: dict) -> tuple[str, dict]:
    visited = set()
    current = name
    while current in icons.get("aliases", {}):
        if current in visited:
            raise ValueError("MDI alias cycle")
        visited.add(current)
        alias = icons["aliases"][current]
        if set(alias) != {"parent"}:
            raise ValueError("MDI alias has unsupported geometry transforms")
        current = alias["parent"]
    icon = icons.get("icons", {}).get(current)
    if not icon:
        raise ValueError(f"No MDI icon named {name!r} in the pinned release")
    if set(icon) - {"body", "hidden"} or (icons.get("width"), icons.get("height")) != (24, 24):
        raise ValueError("Unexpected MDI icon geometry metadata")
    return current, icon


def fetch_icon(name: str, output_dir: Path, *, line_weight="fine", variant="auto", package=None) -> dict:
    if not SAFE_NAME.fullmatch(name):
        raise ValueError("MDI names must contain lowercase letters, digits and hyphens only")
    if line_weight not in {"fine", "original"} or variant not in {"auto", "line", "fill"}:
        raise ValueError("Choose fine or original weight and auto, line or fill variant")
    output_dir.mkdir(parents=True, exist_ok=True)
    icons, info, metadata = package or load_package(output_dir / "source-package")
    canonical_name, icon = resolve_icon(name, icons)
    categories = [category for category, names in metadata.get("categories", {}).items() if canonical_name in names]
    exact = "Brand / Logo" in categories
    # An explicit line declaration lets the host classify unsuffixed line artwork.
    selected_variant = ("line" if canonical_name.endswith("-outline") else "fill") if variant == "auto" else variant
    effective_weight = line_weight if selected_variant == "line" and not exact else "original"
    original_data = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">' + icon["body"] + '</svg>\n').encode()
    validate_svg(original_data)
    source = output_dir / f"mdi-{canonical_name}.svg"
    source.write_bytes(original_data)
    data = original_data
    treatment = {"id": "original", "line_weight": "original" if selected_variant == "line" else None}
    if effective_weight == "fine":
        from slidepoise.icon_geometry import fine_mdi_svg
        try:
            data, treatment = fine_mdi_svg(original_data)
        except ValueError as error:
            raise ValueError(f"Cannot prepare MDI Fine for {name}. Original retained at {source}. Inspect it and choose --line-weight original or another icon. {error}") from error
    output = output_dir / f"mdi-{canonical_name}{'-fine' if effective_weight == 'fine' else ''}.svg"
    output.write_bytes(data)
    asset = {
        "asset_id": output.stem, "canonical_file": str(output.resolve()),
        "requested_icon_name": name, "canonical_icon_name": canonical_name,
        "source_asset_id": source.stem, "source_file": str(source.resolve()),
        "source_sha256": hashlib.sha256(original_data).hexdigest(), "sha256": hashlib.sha256(data).hexdigest(),
        "source_url": f"https://icon-sets.iconify.design/mdi/{canonical_name}/",
        "provider": "Material Design Icons", "provider_version": VERSION,
        "source_package": "@iconify-json/mdi", "source_package_url": PACKAGE_URL, "source_package_integrity": INTEGRITY,
        "author": info["author"], "license": info["license"]["spdx"], "license_url": info["license"]["url"],
        "attribution_notice": "Material Design Icons by Pictogrammers, distributed through Iconify under Apache-2.0.",
        "modification_notice": "Geometry thinned by SlidePoise Fine." if effective_weight == "fine" else None,
        "categories": categories, "style_variant": selected_variant, "geometry_treatment": treatment,
        "original_geometry_reason": "exact_identity_category" if exact else None,
        "intrinsic_aspect_ratio": 1.0, "treatment_recolorable": not exact,
        "recolor_mode": "fill_all", "preserve_canonical_color": exact, "require_exact_identity": exact,
        "persistence": "run_cache_only", "selection_status": "candidate_pending_visual_review",
    }
    output.with_suffix(".provenance.json").write_text(json.dumps(asset, indent=2) + "\n")
    return asset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", nargs="?")
    parser.add_argument("--search", help="Find candidate names and categories in the pinned collection")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--line-weight", choices=("fine", "original"))
    parser.add_argument("--variant", choices=("auto", "line", "fill"), default="auto", help="Auto treats -outline names as line artwork. Declare line only after visually inspecting an unsuffixed icon.")
    args = parser.parse_args()
    source = (json.loads(args.config.read_text()).get("remote_sources") or {}).get("mdi") or {}
    if not source.get("enabled"):
        raise SystemExit("MDI retrieval is disabled in the resolved config")
    if source.get("provider_version", VERSION) != VERSION:
        raise SystemExit(f"This helper supports pinned @iconify-json/mdi {VERSION}")
    try:
        package = load_package(args.output_dir / "source-package")
        if args.search:
            terms = args.search.lower().split()
            categories = package[2].get("categories", {})
            matches = [{"name": name, "categories": [key for key, names in categories.items() if name in names]}
                       for name, icon in sorted(package[0]["icons"].items()) if not icon.get("hidden")
                       and all(term in name or any(term in key.lower() and name in names for key, names in categories.items()) for term in terms)]
            result = {"candidates": matches[:60], "matching_count": len(matches), "selection_owner": "host_agent_visual_reasoning"}
        elif args.name:
            result = fetch_icon(args.name.removeprefix("mdi:"), args.output_dir, line_weight=args.line_weight or source.get("line_weight", "fine"), variant=args.variant, package=package)
        else:
            parser.error("Provide an icon name or --search")
        print(json.dumps(result, indent=2))
    except (ValueError, ImportError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
