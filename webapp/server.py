"""Optional local management console for the SlidePoise framework."""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import shutil
import subprocess
import sys
import tempfile
import hashlib
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from framework.paths import DEFAULT_CONFIG, SKILL_ROOT, active_profiles_root, active_library_sets_root, data_home, node_runtime_root, workspace_root
from framework.profiles import active_profile_id, library_catalog, library_root, list_profiles, profile_record, set_active_profile
from framework import library_sets, components, run_events
from framework import sessions, design, image_generation
from framework import profile_authoring
from framework.storage import ConflictError, revision, update, write
from . import panel
from framework import panel_binding

ROOT = Path(__file__).resolve().parents[1]
SKILL = SKILL_ROOT
UI = Path(__file__).resolve().parent / "ui"
CONSOLE_UI = ROOT / "webapp" / "console"
WORKSPACE = workspace_root()
REGISTRY = WORKSPACE / "runs.json"
LIBRARIES = {"visual_references"}
def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def console_revision():
    """Observe shared files, including edits made directly by an Agent."""
    files = {data_home() / "config.json", data_home() / "settings.json"}
    folders = {active_profiles_root(), active_library_sets_root()}
    for profile in list_profiles():
        folders.add(library_root(profile["id"], "visual_references"))
    for folder in folders:
        files.update(p for p in folder.rglob("*") if p.is_file() and ".history" not in p.parts and p.suffix != ".lock")
    records = []
    for path in sorted(files):
        try:
            stat = path.stat()
            records.append((str(path), stat.st_mtime_ns, stat.st_size))
        except FileNotFoundError:
            continue
    return {"revision": hashlib.sha256(json.dumps(records).encode()).hexdigest()}


def resolve_run(path: str) -> Path:
    return sessions.require_run(path)


def create_run(name: str, location: str | None = None) -> dict[str, Any]:
    return run_summary(sessions.create(name, location, workspace=WORKSPACE, registry_file=REGISTRY))


def run_summary(root: Path, name: str | None = None) -> dict[str, Any]:
    metadata = read_json(root / "session.json", {})
    return {
        **metadata,
        "name": metadata.get("name") or name or root.name,
        "state": metadata.get("state", "active"),
        "requirements": metadata.get("requirements", ""),
        "path": str(root),
        "available": root.is_dir(),
        "uploads": len([path for path in (root / "uploads").glob("*") if path.is_file()]),
        "metadata_revision": revision(root / "session.json"),
        "overrides_revision": revision(root / "session-overrides.json"),
        "defaults_revision": revision(root / "work/session-defaults.json"),
        "defaults_captured_at": read_json(root / "work/session-defaults.json", {}).get("captured_at"),
        "files": [{"name": p.name, "relative": str(p.relative_to(root)), "size": p.stat().st_size} for p in (root / "uploads").glob("*") if p.is_file()],
        "profile": read_json(root / "session-overrides.json", {}).get("profile"),
    }


def library(kind: str, profile_id: str | None = None) -> dict[str, Any]:
    if kind not in LIBRARIES:
        raise ValueError(f"Unknown library: {kind}")
    profile_id = profile_id or active_profile_id()
    catalog_path, catalog = library_catalog(profile_id, kind)
    items = []
    raw_items = catalog.get("items", {})
    values = raw_items.values() if isinstance(raw_items, dict) else raw_items
    for raw in values:
        item = dict(raw)
        item["id"] = str(item.get("id") or item.get("asset_id") or item.get("component_id") or item.get("name"))
        relative = item.get("path") or item.get("preview") or item.get("preview_path") or item.get("file")
        item["asset_url"] = f"/api/library-file?profile={profile_id}&kind={kind}&id={item['id']}" if relative else None
        items.append(item)
    return {"profile_id": profile_id, "kind": kind, "items": items, "count": len(items), "catalog": str(catalog_path), "location": str(catalog_path.parent), "revision": revision(catalog_path)}


def library_path(kind: str, identifier: str, profile_id: str | None = None) -> Path:
    profile_id = profile_id or active_profile_id()
    payload = library(kind, profile_id)
    item = next((value for value in payload["items"] if value["id"] == identifier), None)
    if item is None:
        raise FileNotFoundError(identifier)
    relative = item.get("preview") or item.get("preview_path") or item.get("path") or item.get("file")
    if not relative:
        raise FileNotFoundError(identifier)
    root = library_root(profile_id, kind)
    candidate = (root / str(relative)).resolve()
    if root.resolve() not in candidate.parents or not candidate.is_file():
        raise FileNotFoundError(identifier)
    return candidate


def library_set(set_id: str) -> dict[str, Any]:
    record = library_sets.set_record(set_id)
    _path, catalog = library_sets.set_catalog(set_id)
    raw_items = catalog.get("items", {})
    values = raw_items.values() if isinstance(raw_items, dict) else raw_items
    items = []
    for raw in values:
        item = dict(raw)
        item["id"] = str(item.get("id") or item.get("component_id") or item.get("asset_id") or item.get("name"))
        relative = item.get("preview") or item.get("preview_path") or item.get("path") or item.get("file")
        item["asset_url"] = f"/api/library-set-file?set_id={set_id}&id={item['id']}" if relative else None
        items.append(item)
    return {**record, "items": items, "count": len(items), "revision": library_sets.payload()["revision"]}


def library_set_path(set_id: str, identifier: str) -> Path:
    payload = library_set(set_id)
    if payload.get("source") == "remote":
        raise FileNotFoundError(identifier)
    item = next((value for value in payload["items"] if value["id"] == identifier), None)
    if item is None:
        raise FileNotFoundError(identifier)
    relative = item.get("preview") or item.get("preview_path") or item.get("path") or item.get("file")
    root = Path(payload["root"]).resolve()
    candidate = (root / str(relative)).resolve()
    if root not in candidate.parents or not candidate.is_file():
        raise FileNotFoundError(identifier)
    return candidate


def runtime_health() -> list[dict[str, Any]]:
    from framework.preview_install import preview_status
    preview = preview_status()
    modules = {}
    for name in ("numpy", "cv2"):
        try:
            __import__(name)
            modules[name] = True
        except Exception:
            modules[name] = False
    return [
        {"name": "Python", "available": True, "detail": sys.version.split()[0]},
        {"name": "OpenCV", "available": modules["cv2"] and modules["numpy"], "detail": "Required measurement layer"},
        {"name": "Node", "available": bool(shutil.which("node")), "detail": shutil.which("node") or "Missing"},
        {"name": "PptxGenJS", "available": (node_runtime_root() / "node_modules" / "pptxgenjs" / "package.json").is_file(), "detail": str(node_runtime_root() / "node_modules")},
        {"name": "LibreOffice", "available": bool(preview["office"]), "detail": "Optional preview renderer"},
        {"name": "Poppler", "available": bool(preview["pdftoppm"]), "detail": "Converts rendered PDF pages into slide preview images"},
    ]


def overview() -> dict[str, Any]:
    selected = active_profile_id()
    counts = {"visual_references": library("visual_references", selected)["count"],
              "icon_sets": len(library_sets.list_sets("icons")),
              "component_sets": len(library_sets.list_sets("components"))}
    config_path = data_home() / "config.json"
    config = read_json(config_path if config_path.is_file() else DEFAULT_CONFIG, {})
    return {"libraries": counts, "profiles": list_profiles(), "active_profile": selected, "health": runtime_health(), "schema_version": config.get("schema_version"), "skill_path": str(SKILL), "framework_home": str(data_home())}


def deep_set(document: dict[str, Any], dotted: str, value: Any) -> None:
    cursor = document
    parts = dotted.split(".")
    for part in parts[:-1]:
        cursor = cursor.setdefault(part, {})
    cursor[parts[-1]] = value


def resolved_config(run_root: Path) -> dict[str, Any]:
    return sessions.resolve(run_root)


def run_detail(root):
    cfg = resolved_config(root)
    return {**run_summary(root), "overrides": read_json(root / "session-overrides.json", {}),
            "resolved_config": cfg, "values": design.presentation_values(cfg),
            "profiles": list_profiles(), "fonts": design.FONTS, "densities": design.DENSITIES,
            "style_agency": cfg.get("resolved_profile", {}).get("style_agency", {}),
            "selected_sets": cfg.get("library_sets", {}).get("selected", {"icons": [], "components": []}),
            "library_sets": library_sets.list_sets()}


def library_update(body):
    profile, kind = body["profile"], body["kind"]
    path, catalog = library_catalog(profile, kind)
    def change(catalog):
        items = catalog.setdefault("items", {})
        if body["action"] == "add":
            filename = Path(body["filename"]).name
            if Path(filename).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg", ".pptx", ".json"}:
                raise ValueError("Unsupported resource file type")
            if kind == "icons" and not body.get("license"):
                raise ValueError("Persistent icons need license information")
            identifier = uuid.uuid4().hex[:12]
            filename = identifier + "-" + filename
            (path.parent / filename).write_bytes(base64.b64decode(body["content_base64"], validate=True))
            items[identifier] = {"id": identifier, "name": body.get("name") or body["filename"], "path": filename,
                                 "description": body.get("description", ""), "tags": body.get("tags", []),
                                 "provenance": {"provider": "user_upload", "source_url": body.get("source_url", ""), "license": body.get("license", "")}}
        elif body["action"] == "edit":
            item = next((item for item in items.values() if item.get("id") == body["id"]), None)
            if item is None:
                raise FileNotFoundError(body["id"])
            for key in ("name", "description", "tags"):
                if key in body:
                    item[key] = body[key]
            item.setdefault("provenance", {}).update({key: body[key] for key in ("source_url", "license") if key in body})
        else:
            raise ValueError("Unknown library action")
        return catalog
    update(path, change, expected=body["revision"], default=catalog)
    return library(kind, profile)


class Handler(BaseHTTPRequestHandler):
    server_version = "SlidePoiseConsole/0.5"

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def json_response(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def body(self) -> dict[str, Any]:
        length = min(int(self.headers.get("Content-Length", "0")), 32 * 1024 * 1024)
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def file_response(self, path: Path) -> None:
        payload = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if path.suffix.lower() == ".svg":
            self.send_header("Content-Security-Policy", "sandbox; default-src 'none'; style-src 'unsafe-inline'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/console" or parsed.path.startswith("/console/"):
                return self.console_static(parsed.path)
            if parsed.path == "/api/overview":
                return self.json_response(overview())
            if parsed.path == "/api/console/revision":
                return self.json_response(console_revision())
            if parsed.path == "/api/context":
                return self.json_response({"service": "slidepoise", "profiles": list_profiles(), "active_profile": active_profile_id()})
            if parsed.path == "/api/panel/binding":
                return self.json_response(panel_binding.get(query["id"][0]))
            if parsed.path == "/api/panel":
                return self.json_response(panel.snapshot(resolve_run(query["run"][0])))
            if parsed.path == "/api/run":
                root = resolve_run(query["path"][0])
                return self.json_response(run_detail(root))
            if parsed.path == "/api/design":
                return self.json_response(design.defaults_payload(query.get("profile", [None])[0]))
            if parsed.path == "/api/profile":
                return self.json_response(profile_authoring.profile_payload(query.get("profile", [active_profile_id()])[0]))
            if parsed.path == "/api/health":
                return self.json_response(runtime_health())
            if parsed.path == "/api/settings":
                path = data_home() / "config.json"
                return self.json_response({"config": read_json(path if path.is_file() else DEFAULT_CONFIG), "revision": revision(path)})
            if parsed.path == "/api/generation":
                return self.json_response(image_generation.payload())
            if parsed.path == "/api/library":
                return self.json_response(library(query["kind"][0], query.get("profile", [None])[0]))
            if parsed.path == "/api/library-sets":
                return self.json_response(library_sets.payload())
            if parsed.path == "/api/library-set":
                return self.json_response(library_set(query["set_id"][0]))
            if parsed.path == "/api/component":
                return self.json_response(components.inspect(query["set_id"][0], query["id"][0], int(query["slide"][0]) if "slide" in query else None))
            if parsed.path == "/api/component/source":
                _, _, source = components.source(query["set_id"][0], query["id"][0])
                if source is None:
                    raise FileNotFoundError("No native source")
                return self.file_response(source)
            if parsed.path == "/api/library-set-file":
                return self.file_response(library_set_path(query["set_id"][0], query["id"][0]))
            if parsed.path == "/api/library-file":
                return self.file_response(library_path(query["kind"][0], query["id"][0], query.get("profile", [None])[0]))
            if parsed.path == "/api/artifact":
                root = resolve_run(query["run"][0])
                path = (root / query["path"][0]).resolve()
                if root not in path.parents or not path.is_file():
                    raise FileNotFoundError(path)
                return self.file_response(path)
            return self.static(parsed.path)
        except FileNotFoundError as error:
            return self.json_response({"error": str(error)}, HTTPStatus.NOT_FOUND)
        except Exception as error:  # noqa: BLE001
            return self.json_response({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def do_POST(self) -> None:
        try:
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != self.headers.get("Host"):
                raise ValueError("Cross-origin changes are not allowed")
            body = self.body()
            if self.path == "/api/profile":
                return self.json_response({"status": "ok", "profile": set_active_profile(body["profile_id"]), "overview": overview()})
            if self.path == "/api/profile/create":
                created = profile_authoring.create_profile(body["name"], profile_id=body.get("profile_id"),
                                                           based_on=body.get("based_on", active_profile_id()), purpose=body.get("purpose", ""))
                set_active_profile(created["id"])
                return self.json_response({"profile": profile_authoring.profile_payload(created["id"]), "overview": overview()}, HTTPStatus.CREATED)
            if self.path == "/api/profile/update":
                updated = profile_authoring.update_profile(body["profile_id"], body["values"], body["revision"])
                return self.json_response({"profile": profile_authoring.profile_payload(updated["id"]), "overview": overview()})
            if self.path == "/api/profile/style":
                design.save_profile_style(body["profile"], body.get("values", {}), body.get("profile_values", {}),
                                          body["revision"], body["profile_revision"])
                return self.json_response(design.defaults_payload(body["profile"]))
            if self.path == "/api/profile/reference/add":
                with tempfile.TemporaryDirectory(prefix="slidepoise-reference-") as directory:
                    source = Path(directory) / Path(body["filename"]).name
                    source.write_bytes(base64.b64decode(body["content_base64"], validate=True))
                    result = profile_authoring.add_resource(body["profile_id"], "visual_references", source,
                        name=body.get("name", ""), description=body.get("description", ""))
                return self.json_response(result, HTTPStatus.CREATED)
            if self.path == "/api/profile/reference/update":
                path, _ = library_catalog(body["profile_id"], "visual_references")
                def change_reference(catalog):
                    item = catalog["items"][body["id"]]
                    if {"id", "path", "preview_path", "asset_url"} & set(body["values"]):
                        raise ValueError("Image identity cannot be changed in guidance")
                    item.update(body["values"])
                    return catalog
                update(path, change_reference, expected=body["revision"])
                return self.json_response(library("visual_references", body["profile_id"]))
            if self.path == "/api/library-set/update":
                return self.json_response(library_sets.update_set_metadata(body["set_id"], body["values"], body["revision"]))
            if self.path == "/api/component/object":
                return self.json_response(components.save_object(body["set_id"], body["id"], body["object_id"], body["values"], body["revision"], body.get("slide_number")))
            if self.path == "/api/component/definition":
                return self.json_response(components.update_definition(body["set_id"], body["id"], body["values"], body["revision"]))
            if self.path == "/api/component/open":
                _, _, source = components.source(body["set_id"], body["id"])
                if source is None or source.suffix.lower() != ".pptx":
                    raise ValueError("No native PowerPoint source")
                command = ["open", str(source)] if sys.platform == "darwin" else ["explorer" if sys.platform == "win32" else "xdg-open", str(source)]
                subprocess.Popen(command)
                return self.json_response({"status": "opened"})
            if self.path == "/api/library-set/create":
                return self.json_response(library_sets.create_set(body["name"], body["kind"], body.get("description", "")), HTTPStatus.CREATED)
            if self.path == "/api/library-set/add":
                suffix = Path(body["filename"]).suffix
                with tempfile.NamedTemporaryFile(suffix=suffix) as temporary:
                    temporary.write(base64.b64decode(body["content_base64"], validate=True))
                    temporary.flush()
                    result = library_sets.add_resource(body["set_id"], Path(temporary.name), name=body.get("name") or body["filename"],
                                                       description=body.get("description", ""), tags=body.get("tags", []),
                                                       source_url=body.get("source_url", ""), license_name=body.get("license", ""))
                return self.json_response(result, HTTPStatus.CREATED)
            if self.path == "/api/design":
                design.save_defaults(body["profile"], body.get("values", {}), body["revision"], body.get("reset", False))
                return self.json_response(design.defaults_payload(body["profile"]))
            if self.path == "/api/settings":
                design.save_runtime(body["values"], body["revision"])
                path = data_home() / "config.json"
                return self.json_response({"status": "ok", "config": read_json(path), "revision": revision(path)})
            if self.path == "/api/generation":
                return self.json_response(image_generation.configure(body["values"], body["revision"]))
            if self.path == "/api/run/defaults":
                root = resolve_run(body["run"])
                sessions.adopt_defaults(root, body["revision"])
                return self.json_response(run_detail(root))
            if self.path == "/api/run/design":
                root = resolve_run(body["run"])
                overrides = read_json(root / "session-overrides.json", {})
                if body.get("reset"):
                    overrides.pop("design_overrides", None)
                    overrides.pop("density", None)
                    overrides.pop("palette", None)
                else:
                    patch = design.design_patch(resolved_config(root), body["values"])
                    overrides["design_overrides"] = design.merge(overrides.get("design_overrides", {}), patch)
                sessions.save_overrides(root, overrides, body["revision"])
                return self.json_response(run_detail(root))
            if self.path == "/api/library/update":
                return self.json_response(library_update(body))
            if self.path == "/api/library/location":
                profile_record(body["profile"])
                if body["kind"] not in LIBRARIES:
                    raise ValueError("Only profile visual references have a profile-specific folder")
                root = Path(body["location"]).expanduser().resolve()
                if not (root / "catalog.json").is_file():
                    raise ValueError("Select a folder containing catalog.json. Existing files are never moved.")
                if not isinstance(read_json(root / "catalog.json", {}).get("items"), dict):
                    raise ValueError("Collection catalog must contain an items object")
                def change(cfg):
                    cfg.setdefault("library_locations", {}).setdefault(body["profile"], {})[body["kind"]] = str(root)
                    return cfg
                update(data_home() / "config.json", change, expected=body["revision"], default=read_json(DEFAULT_CONFIG))
                return self.json_response(library(body["kind"], body["profile"]))
            if self.path == "/api/override":
                root = resolve_run(body["run"])
                overrides = read_json(root / "session-overrides.json", {})
                deep_set(overrides, body["key"], body.get("value"))
                sessions.save_overrides(root, overrides, body["revision"])
                return self.json_response(run_detail(root))
            if self.path == "/api/upload":
                root = resolve_run(body["run"])
                target = root / "uploads" / (uuid.uuid4().hex[:8] + "-" + Path(body["filename"]).name)
                target.write_bytes(base64.b64decode(body["content_base64"], validate=True))
                run_events.record(root, "asset_added", f"User added {Path(body['filename']).name}", {"path": str(target)})
                return self.json_response({"status": "ok", "path": str(target)}, HTTPStatus.CREATED)
            raise FileNotFoundError(self.path)
        except ConflictError as error:
            return self.json_response({"error": str(error)}, HTTPStatus.CONFLICT)
        except Exception as error:  # noqa: BLE001
            return self.json_response({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def static(self, requested: str) -> None:
        relative = "index.html" if requested in {"", "/"} else requested.lstrip("/")
        path = (UI / relative).resolve()
        if UI.resolve() not in path.parents or not path.is_file():
            path = UI / "index.html"
        return self.file_response(path)

    def console_static(self, requested: str) -> None:
        relative = requested.removeprefix("/console/") if requested.startswith("/console/") else "index.html"
        relative = relative or "index.html"
        path = (CONSOLE_UI / relative).resolve()
        if CONSOLE_UI.resolve() not in path.parents or not path.is_file():
            path = CONSOLE_UI / "index.html"
        return self.file_response(path)


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True, view: str = "overview") -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), Handler)
    view = "design" if view == "style" else view
    url = f"http://{host}:{port}/console/#{view}"
    print(json.dumps({"status": "running", "url": url, "skill": str(SKILL)}))
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local SlidePoise management console")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--view", choices=["overview", "style", "resources", "system"], default="overview")
    args = parser.parse_args()
    serve(args.host, args.port, not args.no_open, args.view)


if __name__ == "__main__":
    main()
