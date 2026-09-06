#!/usr/bin/env python3
"""List a profile's visual references and selected shared Library Sets."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

KINDS = ("icons", "visual_references", "components")


def default_profiles_root() -> Path:
    installed = Path(os.environ.get("SLIDEPOISE_HOME", Path.home() / ".slidepoise")) / "profiles"
    repository = Path(__file__).resolve().parents[2] / "profiles"
    return installed if installed.is_dir() else repository


def default_sets_root() -> Path:
    installed = Path(os.environ.get("SLIDEPOISE_HOME", Path.home() / ".slidepoise")) / "library-sets"
    repository = Path(__file__).resolve().parents[2] / "library-sets"
    return installed if (installed / "catalog.json").is_file() else repository


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["all", *KINDS], default="all")
    parser.add_argument("--profile")
    parser.add_argument("--config", type=Path, help="Resolved session configuration used by generation")
    parser.add_argument("--profiles-root", type=Path, default=default_profiles_root())
    parser.add_argument("--library-sets-root", type=Path, default=default_sets_root())
    parser.add_argument("--query", default="")
    args = parser.parse_args()

    selected = KINDS if args.kind == "all" else (args.kind,)
    output: dict[str, list[dict]] = {}
    cfg = json.loads(args.config.read_text()) if args.config else None
    if cfg:
        profile = cfg["resolved_profile"]
        args.profile = profile["profile_id"]
        args.library_sets_root = Path(cfg["library_sets"]["root"])
        set_index = cfg["library_sets"]["records"]
        selected_sets = cfg["library_sets"]["selected"]
        visual_catalog = Path(cfg["libraries"]["visual_references"]["catalog"])
    else:
        if not args.profile:
            parser.error("Use --config for a session, or --profile to browse a shared profile")
        profile = json.loads((args.profiles_root / args.profile / "profile.json").read_text(encoding="utf-8"))
        set_index = json.loads((args.library_sets_root / "catalog.json").read_text(encoding="utf-8")).get("items", {})
        selected_sets = profile.get("library_sets", {})
        visual_catalog = args.profiles_root / args.profile / "libraries/visual_references/catalog.json"
    for kind in selected:
        catalogs = []
        if kind == "visual_references":
            catalogs = [(visual_catalog, None)]
        else:
            for set_id in selected_sets.get(kind, []):
                record = set_index.get(set_id, {})
                if record.get("source") == "local":
                    catalogs.append((args.library_sets_root / record["root"] / "catalog.json", set_id))
                else:
                    if cfg and not cfg.get("remote_sources", {}).get(record.get("provider"), {}).get("enabled"):
                        continue
                    output.setdefault(kind, []).append({"set_id": set_id, "name": record.get("name"), "source": "remote", "provider": record.get("provider")})
        records: list[dict] = []
        for catalog_path, set_id in catalogs:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            for key, item in (catalog.get("items") or {}).items():
                haystack = " ".join([str(item.get("id", "")), str(item.get("name", "")), str(item.get("description", "")), " ".join(map(str, item.get("tags", []) or []))]).lower()
                terms = [term for term in args.query.lower().split() if term]
                if terms and not all(term in haystack for term in terms):
                    continue
                record = dict(item)
                asset_path = catalog_path.parent / str(item.get("preview_path") or item.get("path", key))
                record["absolute_path"] = str(asset_path.resolve()) if asset_path.exists() else None
                record["profile_id"] = args.profile
                if set_id:
                    record["set_id"] = set_id
                records.append(record)
        output.setdefault(kind, []).extend(records)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
