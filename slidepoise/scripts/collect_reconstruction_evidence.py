#!/usr/bin/env python3
"""Collect objective reconstruction-contract and config consistency facts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime/src"))
from slidepoise.canvas import reconstruction_geometry, validate_derived_canvas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--measured-scene", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    measured = json.loads(args.measured_scene.read_text(encoding="utf-8"))
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    errors: list[dict] = []

    if not measured.get("runtime", {}).get("opencv"):
        errors.append({"reason": "fresh_OpenCV_measurement_missing"})
    local_norm = measured.get("runtime", {}).get("local_geometry_normalization", {}) or {}
    if local_norm.get("enabled") is not True:
        errors.append({"reason": "mandatory_local_geometry_normalization_missing"})
    if "fixture://" in args.measured_scene.read_text(encoding="utf-8").lower():
        errors.append({"reason": "fixture_measurement_forbidden"})

    design = config["design"]
    header = design["frame"]["header"]
    footer = design["frame"]["footer"]
    try:
        validate_derived_canvas(config)
        source = measured["source"]
        expected_geometry = reconstruction_geometry(design, [source["width_px"], source["height_px"]])
        for key, expected in expected_geometry.items():
            if contract.get(key) != expected:
                errors.append({"reason": "reconstruction_canvas_mismatch", "field": key, "expected": expected, "actual": contract.get(key)})
    except ValueError as error:
        errors.append({"reason": "invalid_reconstruction_canvas", "detail": str(error)})
    frame = contract.get("frame_configuration", {})
    for area, expected in (("header", header), ("footer", footer)):
        actual = frame.get(area, {})
        for key in ("enabled", "height_px", "implementation"):
            if actual.get(key) != expected.get(key):
                errors.append({"reason": "frame_configuration_mismatch", "area": area, "field": key, "expected": expected.get(key), "actual": actual.get(key)})

    allowed = set(design.get("connectors", {}).get("allowed_families", []))
    for plan in contract.get("connector_reconstruction_plans", []):
        if plan.get("connector_family") not in allowed:
            errors.append({"reason": "unsupported_connector_family", "connector": plan.get("entity_id")})
    for mapping in contract.get("canonical_asset_mappings", []):
        if not Path(mapping.get("selected_asset_path", "")).is_file():
            errors.append({"reason": "missing_canonical_asset", "entity": mapping.get("entity_id"), "path": mapping.get("selected_asset_path")})

    report = {
        "evidence_type": "objective_reconstruction_contract_facts",
        "blocking_facts": errors,
        "agent_interpretation_required": True,
        "note": "No reconstruction verdict is produced. The host Agent interprets these facts together with the accepted target and render.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if not errors else 2)


if __name__ == "__main__":
    main()
