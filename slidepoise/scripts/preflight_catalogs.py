#!/usr/bin/env python3
"""Collect objective external-profile catalog and asset-path preflight facts."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

KINDS = ("visual_references",)


def default_profiles_root() -> Path:
    installed = Path(os.environ.get("SLIDEPOISE_HOME", Path.home() / ".slidepoise")) / "profiles"
    repository = Path(__file__).resolve().parents[2] / "profiles"
    return installed if installed.is_dir() else repository


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles-root", type=Path, default=default_profiles_root())
    parser.add_argument("--profile")
    parser.add_argument("--library-sets-root", type=Path)
    args = parser.parse_args()
    profile_dirs = [args.profiles_root / args.profile] if args.profile else sorted(path.parent for path in args.profiles_root.glob("*/profile.json"))
    errors: list[str] = []
    counts: dict[str, dict[str, int]] = {}
    if not args.profiles_root.is_dir():
        errors.append(f"profiles folder missing: {args.profiles_root}")
    elif not profile_dirs:
        errors.append(f"no profiles found in: {args.profiles_root}")
    sets_root = args.library_sets_root or (args.profiles_root.parent / "library-sets")
    if args.library_sets_root is None and not (sets_root / "catalog.json").is_file():
        sets_root = Path(__file__).resolve().parents[2] / "library-sets"
    if (sets_root / "catalog.json").is_file():
        set_index = json.loads((sets_root / "catalog.json").read_text(encoding="utf-8")).get("items", {})
    else:
        errors.append(f"library sets catalog missing: {sets_root / 'catalog.json'}")
        set_index = {}
    for profile_dir in profile_dirs:
        profile_path = profile_dir / "profile.json"
        if not profile_path.is_file():
            errors.append(f"missing profile: {profile_path}")
            continue
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile_id = str(profile.get("profile_id") or profile_dir.name)
        profile_counts: dict[str, int] = {}
        selected_sets = profile.get("library_sets", {})
        for set_kind in ("icons", "components"):
            ids = selected_sets.get(set_kind, [])
            if not isinstance(ids, list):
                errors.append(f"{profile_id}:library_sets.{set_kind}: must be a list")
                continue
            for set_id in ids:
                record = set_index.get(set_id)
                if not record or record.get("kind") != set_kind:
                    errors.append(f"{profile_id}:library_sets.{set_kind}: unknown set {set_id}")
            profile_counts[f"{set_kind.removesuffix('s')}_sets"] = len(ids)
        for kind in KINDS:
            catalog_path = profile_dir / "libraries" / kind / "catalog.json"
            if not catalog_path.is_file():
                errors.append(f"{profile_id}:{kind}: missing catalog")
                continue
            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            items = data.get("items", {})
            if not isinstance(items, dict):
                errors.append(f"{profile_id}:{kind}: items must be an object")
                continue
            seen: set[str] = set()
            registered_assets: set[Path] = set()
            asset_root = catalog_path.parent.resolve()
            for key, record in items.items():
                identifier = str(record.get("id") or "")
                if not identifier or identifier in seen:
                    errors.append(f"{profile_id}:{kind}:{key}: missing or duplicate id")
                seen.add(identifier)
                relative = record.get("path")
                if relative:
                    target = (catalog_path.parent / str(relative)).resolve()
                    if not target.is_relative_to(asset_root):
                        errors.append(f"{profile_id}:{kind}:{key}: asset escapes its library {relative}")
                    elif not target.is_file():
                        errors.append(f"{profile_id}:{kind}:{key}: missing asset {relative}")
                    else:
                        registered_assets.add(target)
            unregistered = sorted(
                path.relative_to(catalog_path.parent).as_posix()
                for path in catalog_path.parent.rglob("*")
                if path.is_file() and path != catalog_path and not path.name.startswith(".")
                and path.resolve() not in registered_assets
            )
            for relative in unregistered:
                errors.append(f"{profile_id}:{kind}: unregistered asset {relative}")
            profile_counts[kind] = len(items)
        counts[profile_id] = profile_counts
    for set_id, record in set_index.items():
        if record.get("source") != "local":
            continue
        catalog_path = sets_root / record.get("root", "") / "catalog.json"
        if not catalog_path.is_file():
            errors.append(f"library-set:{set_id}: missing catalog")
    report = {
        "evidence_type": "objective_catalog_structure",
        "agent_interpretation_required": True,
        "counts": counts,
        "blocking_facts": errors,
        "notice": "No overall verdict is produced. The host Agent still judges relevance, style, and visual quality."
    }
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if not errors else 2)


if __name__ == "__main__":
    main()
