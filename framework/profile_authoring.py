"""User-owned guidance profile authoring shared by Agents and the Console."""
from __future__ import annotations

import copy
import re
import shutil
import tempfile
import uuid
from pathlib import Path

from .paths import data_home
from .profiles import canonical_profile_id, active_profile_id, library_catalog, library_root, profile_record
from .storage import read, revision, update, write


KINDS = {
    "visual_references": {".png", ".jpg", ".jpeg", ".webp"},
}


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    if not result or len(result) > 60:
        raise ValueError("Use a short profile name with letters or numbers")
    return result


def create_profile(name: str, *, profile_id: str | None = None, based_on: str | None = None, purpose: str = "") -> dict:
    based_on = canonical_profile_id(based_on or active_profile_id())
    identifier = slug(profile_id or name)
    root = data_home() / "profiles" / identifier
    if root.exists():
        raise FileExistsError(f"Profile already exists: {identifier}")
    source = Path(profile_record(based_on)["root"])
    references = library_root(based_on, "visual_references")
    profile = read(source / "profile.json", {})
    from .design import merge
    configured = read(data_home() / "config.json", {}).get("user_design_overrides", {}).get(based_on, {})
    profile["design_overrides"] = merge(profile.get("design_overrides", {}), configured)
    profile.update({"profile_id": identifier, "name": name.strip(), "purpose": purpose.strip() or f"A user-authored presentation style based on {based_on}."})
    profile["origin"] = {"type": "user_authored", "based_on": based_on}
    root.parent.mkdir(parents=True, exist_ok=True)
    # Keep the copy invisible to profile discovery until its identity is distinct.
    with tempfile.TemporaryDirectory(prefix="profile-create-", dir=data_home()) as directory:
        staged = Path(directory) / "profile"
        shutil.copytree(source, staged)
        if references.resolve() != (source / "libraries/visual_references").resolve():
            shutil.copytree(references, staged / "libraries/visual_references", dirs_exist_ok=True)
        write(staged / "profile.json", profile)
        staged.rename(root)
    return profile_record(identifier)


def apply_profile_values(profile_id: str, profile: dict, values: dict) -> dict:
    """Validate a profile edit without writing any files."""
    if not isinstance(values, dict) or any(not re.fullmatch(r"[a-z][a-z0-9_]*", key) for key in values):
        raise ValueError("Profile fields must use lower-case names")
    if {"profile_id", "schema_version"} & set(values):
        raise ValueError("Profile identity and schema version cannot be changed here")
    if "library_sets" in values:
        from .library_sets import set_record
        selections = values["library_sets"]
        if not isinstance(selections, dict) or set(selections) - {"icons", "components"}:
            raise ValueError("Choose icon or component sets")
        for kind, identifiers in selections.items():
            if not isinstance(identifiers, list) or any(not isinstance(identifier, str) or set_record(identifier)["kind"] != kind for identifier in identifiers):
                raise ValueError("A selected set has the wrong resource type")
    result = copy.deepcopy(profile)
    for key, value in values.items():
        if key in {"name", "purpose"} and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{key} must be meaningful text")
        result[key] = copy.deepcopy(value)
    result["profile_id"] = profile_id
    return result


def update_profile(profile_id: str, values: dict, expected: str) -> dict:
    profile_id = canonical_profile_id(profile_id)
    path = Path(profile_record(profile_id)["path"])
    update(path, lambda profile: apply_profile_values(profile_id, profile, values), expected=expected, default={})
    return profile_record(profile_id)


def profile_payload(profile_id: str) -> dict:
    record = profile_record(profile_id)
    return {**record, "revision": revision(Path(record["path"]))}


def add_resource(profile_id: str, kind: str, source: Path, *, name: str, description: str,
                 tags: list[str] | None = None, source_url: str = "", license_name: str = "") -> dict:
    if kind not in KINDS:
        raise ValueError("Unknown resource kind")
    source = source.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in KINDS[kind]:
        raise ValueError(f"Unsupported {kind} file")
    catalog_path, _ = library_catalog(profile_id, kind)
    identifier = uuid.uuid4().hex[:12]
    destination = catalog_path.parent / f"{identifier}-{source.name}"
    shutil.copy2(source, destination)
    def change(catalog):
        catalog.setdefault("items", {})[identifier] = {
            "id": identifier,
            "name": name.strip() or source.stem,
            "description": description.strip(),
            "tags": tags or [],
            "path": destination.name,
            "provenance": {"provider": "user_or_agent_added", "source_url": source_url, "license": license_name},
        }
        return catalog
    update(catalog_path, change, default={"items": {}})
    return {"id": identifier, "path": str(destination), "profile": profile_id, "kind": kind}
