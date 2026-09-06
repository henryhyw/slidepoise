#!/usr/bin/env python3
"""Manage a selected external profile library without mutating the stable skill."""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

KINDS = {
    "icon": ("icons", {".svg", ".png"}),
    "visual_reference": ("visual_references", {".png", ".jpg", ".jpeg", ".webp"}),
    "component": ("components", {".json", ".svg", ".png", ".pptx"}),
}


def default_profiles_root() -> Path:
    return Path(os.environ.get("SLIDEPOISE_HOME", Path.home() / ".slidepoise")) / "profiles"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage one profile-private SlidePoise library.")
    parser.add_argument("--profiles-root", type=Path, default=default_profiles_root())
    parser.add_argument("--profile", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("--kind", choices=KINDS, required=True)
    add.add_argument("--file", type=Path, required=True)
    add.add_argument("--id", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--description", required=True)
    add.add_argument("--tags", default="")
    add.add_argument("--source", default="user_or_project_asset")
    add.add_argument("--source-url", default="")
    add.add_argument("--license", default="")
    remove = sub.add_parser("remove")
    remove.add_argument("--kind", choices=KINDS, required=True)
    remove.add_argument("--id", required=True)
    args = parser.parse_args()

    library_name, extensions = KINDS[args.kind]
    root = args.profiles_root.expanduser().resolve() / args.profile / "libraries" / library_name
    catalog_path = root / "catalog.json"
    if not catalog_path.is_file():
        raise SystemExit(f"Profile library is missing: {catalog_path}")
    catalog = load(catalog_path)
    items = catalog.setdefault("items", {})

    if args.command == "add":
        source = args.file.expanduser().resolve()
        if source.suffix.lower() not in extensions:
            raise SystemExit(f"{args.kind} requires one of {sorted(extensions)}")
        if args.kind == "icon" and not args.license:
            raise SystemExit("Persistent profile icons require explicit --license provenance")
        if any(str(record.get("id")) == args.id for record in items.values()):
            raise SystemExit(f"Asset id already exists: {args.id}")
        destination = root / source.name
        shutil.copy2(source, destination)
        record = {
            "id": args.id,
            "path": destination.name,
            "name": args.name,
            "description": args.description,
            "tags": [value.strip() for value in args.tags.split(",") if value.strip()],
            "provenance": {"provider": args.source, "source_url": args.source_url, "license": args.license},
        }
        items[args.id] = record
        save(catalog_path, catalog)
        print(json.dumps(record, indent=2, ensure_ascii=False))
        return

    found = next(((key, record) for key, record in items.items() if str(record.get("id")) == args.id), None)
    if found is None:
        raise SystemExit(f"Asset not found: {args.id}")
    key, record = found
    path = root / str(record.get("path") or "")
    if path.is_file():
        path.unlink()
    del items[key]
    save(catalog_path, catalog)
    print(json.dumps({"removed": args.id, "profile": args.profile}, indent=2))


if __name__ == "__main__":
    main()
