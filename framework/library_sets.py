"""Shared icon and component sets used by guidance profiles and the Console."""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import uuid
from typing import Any

from .paths import active_library_sets_root
from .storage import read, revision, update


SET_KINDS = {"icons", "components"}


def catalog_path() -> Path:
    return active_library_sets_root() / "catalog.json"


def list_sets(kind: str | None = None) -> list[dict[str, Any]]:
    payload = read(catalog_path(), {"items": {}})
    values = payload.get("items", {}).values()
    result = []
    for raw in values:
        item = dict(raw)
        if kind and item.get("kind") != kind:
            continue
        item["id"] = str(item["id"])
        item["root"] = str((active_library_sets_root() / item.get("root", "")).resolve())
        result.append(item)
    return sorted(result, key=lambda item: (item.get("kind", ""), item.get("name", "")))


def set_record(set_id: str) -> dict[str, Any]:
    for item in list_sets():
        if item["id"] == set_id:
            return item
    raise FileNotFoundError(f"Unknown library set: {set_id}")


def set_catalog(set_id: str) -> tuple[Path, dict[str, Any]]:
    record = set_record(set_id)
    if record.get("source") == "remote":
        return catalog_path(), {"items": {}}
    path = Path(record["root"]) / "catalog.json"
    return path, read(path, {"items": {}})


def profile_set_ids(profile: dict[str, Any], kind: str) -> list[str]:
    if kind not in SET_KINDS:
        raise ValueError(f"Unknown set kind: {kind}")
    value = profile.get("library_sets", {}).get(kind, [])
    return [str(item) for item in value if any(record["id"] == str(item) and record["kind"] == kind for record in list_sets(kind))]


def payload() -> dict[str, Any]:
    return {"sets": list_sets(), "revision": revision(catalog_path()), "location": str(active_library_sets_root())}


def update_set_metadata(set_id: str, values: dict[str, Any], expected: str) -> dict[str, Any]:
    allowed = {"name", "description"}
    if set(values) - allowed:
        raise ValueError("Unsupported library set field")
    def change(document):
        item = document.setdefault("items", {}).get(set_id)
        if item is None:
            raise FileNotFoundError(set_id)
        for key, value in values.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key} must be meaningful text")
            item[key] = value.strip()
        return document
    update(catalog_path(), change, expected=expected, default={"items": {}})
    return payload()


def create_set(name: str, kind: str, description: str = "") -> dict[str, Any]:
    if kind not in SET_KINDS:
        raise ValueError("Library Sets may contain icons or components")
    identifier = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    if not identifier:
        raise ValueError("Use a meaningful set name")
    root = active_library_sets_root()
    folder = root / kind / identifier
    if folder.exists() or any(item["id"] == identifier for item in list_sets()):
        raise FileExistsError(f"Library Set already exists: {identifier}")
    folder.mkdir(parents=True)
    from .storage import write
    write(folder / "catalog.json", {"schema_version": "1.0.0", "items": {}})
    def change(document):
        document.setdefault("items", {})[identifier] = {"id": identifier, "kind": kind, "name": name.strip(), "description": description.strip(), "source": "local", "root": f"{kind}/{identifier}"}
        return document
    update(catalog_path(), change, default={"schema_version": "1.0.0", "items": {}})
    return set_record(identifier)


def add_resource(set_id: str, source: Path, *, name: str, description: str = "", tags: list[str] | None = None,
                 source_url: str = "", license_name: str = "") -> dict[str, Any]:
    record = set_record(set_id)
    if record.get("source") != "local":
        raise ValueError("Remote Library Sets retrieve assets at run time")
    source = source.expanduser().resolve()
    allowed = {"icons": {".svg", ".png"}, "components": {".json", ".svg", ".png", ".pptx"}}[record["kind"]]
    if not source.is_file() or source.suffix.lower() not in allowed:
        raise ValueError("Unsupported Library Set resource")
    if record["kind"] == "icons" and not license_name:
        raise ValueError("Persistent icons require license information")
    path, _catalog = set_catalog(set_id)
    identifier = uuid.uuid4().hex[:12]
    destination = path.parent / f"{identifier}-{source.name}"
    metadata = {}
    if record["kind"] == "components":
        if source.suffix.lower() == ".pptx":
            from pptx import Presentation
            deck = Presentation(source)
            if not len(deck.slides):
                raise ValueError("The PowerPoint has no slides")
            metadata = {"path": destination.name, "preview_path": destination.with_suffix(".preview.png").name,
                        "native_source_slide_number": 1, "resource_form": "native_powerpoint"}
        elif source.suffix.lower() == ".json":
            definition = read(source)
            if not isinstance(definition, dict):
                raise ValueError("Component guidance must be a JSON object")
            metadata = {"definition_path": destination.name, "resource_form": "grammar_only", "grammar": definition}
        else:
            metadata = {"preview_path": destination.name, "resource_form": "visual_precedent"}
    else:
        metadata = {"path": destination.name}
    shutil.copy2(source, destination)
    def change(document):
        document.setdefault("items", {})[identifier] = {"id": identifier, "name": name.strip() or source.stem, "description": description.strip(), "tags": tags or [], **metadata, "provenance": {"provider": "user_or_agent_added", "source_url": source_url, "license": license_name}}
        return document
    update(path, change, default={"schema_version": "1.0.0", "items": {}})
    return {"id": identifier, "set_id": set_id, "path": str(destination)}
