"""Read the lightweight, run-bound style and asset panel state."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

from framework import run_events
from framework.storage import revision


def file_record(root: Path, path: Path) -> dict | None:
    path = path.resolve()
    if root not in path.parents or not path.is_file():
        return None
    stat = path.stat()
    relative = str(path.relative_to(root))
    return {
        "path": relative,
        "name": path.name,
        "url": "/api/artifact?" + urlencode({"run": str(root), "path": relative, "v": stat.st_mtime_ns}),
        "modified": stat.st_mtime,
        "version": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def snapshot(root: Path) -> dict:
    root = root.resolve()
    materials = [record for path in sorted((root / "uploads").glob("*"))
                 if (record := file_record(root, path))]
    result = {
        "path": str(root),
        "materials": materials,
        "pending_events": run_events.pending(root),
        "settings_revisions": {
            name: revision(root / name)
            for name in ("session-overrides.json", "work/session-defaults.json")
        },
    }
    result["revision"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, default=str).encode()
    ).hexdigest()
    return result
