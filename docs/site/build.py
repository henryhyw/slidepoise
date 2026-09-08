#!/usr/bin/env python3
"""Validate real showcase artifacts and produce a portable static site bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


SITE = Path(__file__).resolve().parent
ROOT = SITE.parents[1]
STATIC_FILES = (
    "index.html", "styles.css", "app.mjs", "mark.svg", "showcases.json",
    "object-inspector.mjs", "object-inspector.css", "planning-viewer.mjs", "reconstruction-viewer.mjs", "architecture.svg", "architecture.png",
)
SLIDE_ARTIFACTS = ("target", "render", "thumbnail", "scene", "evidence", "objects", "semantic", "measurement", "measurement_overlay")
WORKFLOW_STAGES = ("plan", "design", "reconstruct", "review")


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path.relative_to(ROOT)}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_file(value: str, base: Path, boundary: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"An artifact path is missing in {base.relative_to(ROOT)}")
    url = urlsplit(value)
    if url.scheme or url.netloc or url.query or url.fragment or Path(value).is_absolute():
        raise ValueError(f"Expected a relative local artifact path, received {value!r}")
    path = (base / value).resolve()
    if not path.is_relative_to(boundary):
        raise ValueError(f"Artifact escapes its source directory: {value}")
    if not path.is_file() or not path.stat().st_size:
        raise ValueError(f"Missing or empty artifact: {path.relative_to(ROOT)}")
    return path


def validate_object_binding(document: dict, slide: dict, page: int,
                            pptx_path: str, pptx_hash: str, render_hash: str) -> None:
    """Reject geometry extracted from a different slide or an earlier deliverable."""
    identity = slide["id"]
    if document.get("schema_version") != 1 or not isinstance(document.get("objects"), list):
        raise ValueError(f"Invalid object document for slide {identity}")
    object_ids = [item.get("id") if isinstance(item, dict) else None for item in document["objects"]]
    if any(not isinstance(value, str) or not value for value in object_ids) or len(set(object_ids)) != len(object_ids):
        raise ValueError(f"Missing or duplicate browser object ids for slide {identity}")
    if document.get("slide_id") != identity or document.get("page_number") != page:
        raise ValueError(f"Object slide identity or page order does not match {identity}")
    source = document.get("source")
    if not isinstance(source, dict):
        raise ValueError(f"Missing object source binding for slide {identity}")
    expected = {
        "pptx": {"path": pptx_path, "sha256": pptx_hash},
        "render": {"path": slide["render"], "sha256": render_hash},
    }
    for kind, binding in expected.items():
        actual = source.get(kind)
        if not isinstance(actual, dict) or any(actual.get(key) != value for key, value in binding.items()):
            raise ValueError(f"Object {kind} binding is stale or mismatched for slide {identity}")


def validate_canvas(value: dict | None) -> None:
    """A generated body may occupy a region of a larger rendered slide."""
    if value is None:
        return
    if not isinstance(value, dict):
        raise ValueError("Canvas must describe a full slide and its content region")
    full = value.get("full_slide_px")
    region = value.get("content_region_px")
    if not isinstance(full, list) or len(full) != 2 or not isinstance(region, list) or len(region) != 4:
        raise ValueError("Canvas requires two full-slide dimensions and four content-region coordinates")
    if any(isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number)
           for number in full + region):
        raise ValueError("Canvas dimensions and coordinates must be finite numbers")
    if (min(full) <= 0 or min(region[:2]) < 0 or min(region[2:]) <= 0
            or region[0] + region[2] > full[0] or region[1] + region[3] > full[1]):
        raise ValueError("Canvas content region must fit inside the full slide")


def validate_site_model(index: dict, manifests: list[Path]) -> None:
    """Bind the public explanation to the same real artifacts as the viewer."""
    decks = {read_json(path)["id"]: (path, read_json(path)) for path in manifests}
    workflows = index.get("workflow")
    if not isinstance(workflows, dict) or set(workflows) != set(decks):
        raise ValueError("Workflow configuration must cover the listed samples")
    for identity, (_, deck) in decks.items():
        groups = workflows[identity]
        if (not isinstance(groups, dict) or set(groups) != set(WORKFLOW_STAGES)
                or any(not isinstance(groups[stage], list) for stage in WORKFLOW_STAGES)):
            raise ValueError("Each sample must use the four shared workflow stages")
        assigned = [path for stage in WORKFLOW_STAGES for path in groups[stage]]
        actual = [step["artifact"] for step in deck["process"]]
        if (any(not isinstance(path, str) for path in assigned)
                or len(assigned) != len(set(assigned)) or sorted(assigned) != sorted(actual)):
            raise ValueError("Workflow must assign every retained artifact exactly once")

    labels = index.get("artifact_labels")
    if labels is not None:
        if not isinstance(labels, dict) or set(labels) != set(decks):
            raise ValueError("Artifact labels must cover the listed samples")
        for identity, (_, deck) in decks.items():
            mapping = labels[identity]
            paths = {step["artifact"] for step in deck["process"]}
            if (not isinstance(mapping, dict) or set(mapping) != paths
                    or any(not isinstance(label, str) or not label.strip() for label in mapping.values())):
                raise ValueError("Artifact labels must name the retained process files")
    summaries = index.get("presentation_summaries")
    if summaries is not None and (not isinstance(summaries, dict) or set(summaries) != set(decks)
                                  or any(not isinstance(value, str) or not value.strip() for value in summaries.values())):
        raise ValueError("Presentation summaries must describe the listed samples")

    briefs = index.get("brief_sources")
    if not isinstance(briefs, dict) or set(briefs) != set(decks):
        raise ValueError("Presentation briefs must cover the listed samples")
    for identity, (manifest, deck) in decks.items():
        if briefs[identity] not in workflows[identity]["plan"]:
            raise ValueError("Presentation brief must be a retained planning artifact")
        outline = read_json(local_file(briefs[identity], manifest.parent, manifest.parent))
        active = [item for item in outline.get("slides", []) if item.get("disposition") != "omitted"]
        if (not isinstance(outline.get("throughline"), str) or not outline["throughline"].strip()
                or [item.get("slide_id") for item in active] != [item["id"] for item in deck["slides"]]
                or any(not isinstance(item.get("dominant_message"), str) or not item["dominant_message"].strip() for item in active)):
            raise ValueError("Presentation brief must describe the actual slides in order")

    planning = index.get("planning_inputs")
    if not isinstance(planning, dict) or set(planning) != set(decks):
        raise ValueError("Full planning inputs must cover the listed samples")
    for identity, (manifest, deck) in decks.items():
        pages = planning[identity]
        if not isinstance(pages, dict) or set(pages) != {item["id"] for item in deck["slides"]}:
            raise ValueError("Full planning inputs must cover every slide")
        outline = read_json(local_file(briefs[identity], manifest.parent, manifest.parent))
        messages = {item["slide_id"]: item["dominant_message"] for item in outline["slides"]}
        for slide_id, inputs in pages.items():
            if not isinstance(inputs, dict):
                raise ValueError("A full slide input is missing")
            intent = read_json(local_file(inputs.get("intent"), manifest.parent, manifest.parent))
            required = intent.get("required_content")
            if (intent.get("dominant_message") != messages[slide_id] or not isinstance(required, list)
                    or not required or any(not isinstance(item, (str, dict)) or not item for item in required)):
                raise ValueError("Full slide input must contain its matching message and required content")
            sources = inputs.get("inputs")
            if not isinstance(sources, list) or not sources:
                raise ValueError("Every slide needs its retained image-generation input")
            for source in sources:
                if not isinstance(source, dict) or not isinstance(source.get("label"), str) or not source["label"].strip():
                    raise ValueError("Image-generation inputs need descriptive labels")
                path = local_file(source.get("path"), manifest.parent, manifest.parent)
                if path.suffix == ".json":
                    record = read_json(path)
                    prompt = record.get("prompt")
                    if not isinstance(prompt, str) or not prompt.strip():
                        raise ValueError("Recorded generation requests must contain their prompt")
                    expected = record.get("prompt_sha256")
                    if expected and expected != hashlib.sha256(prompt.encode("utf-8")).hexdigest():
                        raise ValueError("Recorded generation prompt hash does not match its content")
                elif path.suffix != ".txt" or not path.read_text(encoding="utf-8").strip():
                    raise ValueError("Recorded generation input must be a prompt request or text file")

    walkthrough = index.get("walkthrough")
    if walkthrough is None:
        return
    if not isinstance(walkthrough, dict) or walkthrough.get("showcase_id") not in decks:
        raise ValueError("Walkthrough must use a listed sample")
    manifest, deck = decks[walkthrough["showcase_id"]]
    slide = next((item for item in deck["slides"] if item["id"] == walkthrough.get("slide_id")), None)
    if not slide or not slide.get("objects") or not slide.get("evidence"):
        raise ValueError("Walkthrough needs a real slide with native objects and semantic evidence")
    sources = {}
    for key in ("intent", "semantic", "measurement", "measurement_image"):
        path = local_file(walkthrough.get(key), manifest.parent, manifest.parent)
        if key != "measurement_image":
            sources[key] = read_json(path)
    entity_id = walkthrough.get("entity_id")
    semantic = next((item for item in sources["semantic"].get("entities", [])
                     if item.get("id") == entity_id and item.get("kind") == "chart"), None)
    measured = next((item for item in sources["measurement"].get("entities", [])
                     if item.get("id") == entity_id), None)
    document = read_json(local_file(slide["objects"], manifest.parent, manifest.parent))
    native = next((item for item in document["objects"]
                   if item.get("name") == entity_id and item.get("kind") == "chart"), None)
    brief = next((item for item in sources["intent"].get("required_content", [])
                  if item.get("role") == "native_chart"), None)
    if not semantic or not measured or not native or not brief:
        raise ValueError("Walkthrough must follow one chart through intent, meaning, measurement and PowerPoint")
    structure = semantic.get("chart_structure", {})
    native_series = native.get("chart", {}).get("series", [])
    mapped_series = structure.get("series", [])
    if len(native_series) != 1 or len(mapped_series) != 1 or not brief.get("categories"):
        raise ValueError("The walkthrough requires a populated single-series chart")

    def categories(values: list) -> list[str]:
        return [" ".join(str(value).split()) for value in values]

    if (categories(brief.get("categories", [])) != categories(structure.get("categories", []))
            or categories(structure.get("categories", [])) != categories(native_series[0].get("categories", []))
            or brief.get("values") != mapped_series[0].get("values")
            or mapped_series[0].get("values") != native_series[0].get("values")):
        raise ValueError("Walkthrough chart data differs between its explanation and actual PowerPoint")
    measured_box = measured.get("measurement", {}).get("visible_bbox", {}).get("px")
    for box in (semantic.get("bbox_hint"), measured_box):
        if (not isinstance(box, list) or len(box) != 4
                or any(isinstance(value, bool) or not isinstance(value, (int, float))
                       or not math.isfinite(value) for value in box)
                or min(box[:2]) < 0 or min(box[2:]) <= 0):
            raise ValueError("Walkthrough needs actual authored and measured chart bounds")
    target = local_file(slide["target"], manifest.parent, manifest.parent)
    if sources["semantic"].get("provenance", {}).get("source_sha256") != sha256(target):
        raise ValueError("Walkthrough semantic evidence belongs to a different target image")


def validate() -> list[Path]:
    index = read_json(SITE / "showcases.json")
    entries = index.get("showcases")
    if not isinstance(entries, list) or not entries:
        raise ValueError("The showcase index must list at least one manifest")
    manifests = []
    deck_ids = set()
    for entry in entries:
        manifest = local_file(entry, SITE, ROOT / "examples")
        data = read_json(manifest)
        if not isinstance(data.get("id"), str) or not data["id"] or data["id"] in deck_ids:
            raise ValueError(f"Missing or duplicate presentation id in {manifest.relative_to(ROOT)}")
        deck_ids.add(data["id"])
        validate_canvas(data.get("canvas"))
        for key in ("title", "summary"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                raise ValueError(f"Missing {key} in {manifest.relative_to(ROOT)}")
        slides = data.get("slides")
        if not isinstance(slides, list) or not slides:
            raise ValueError(f"Missing slide list in {manifest.relative_to(ROOT)}")
        downloads = data.get("downloads", {})
        if not isinstance(downloads, dict) or not downloads.get("pptx"):
            raise ValueError(f"An editable PowerPoint download is required in {data['id']}")
        for value in downloads.values():
            local_file(value, manifest.parent, manifest.parent)
        pptx_hash = sha256(local_file(downloads["pptx"], manifest.parent, manifest.parent))
        slide_ids = set()
        for page, slide in enumerate(slides, start=1):
            if not isinstance(slide, dict) or not slide.get("id") or not slide.get("title"):
                raise ValueError(f"Every slide needs an id and title in {data['id']}")
            if slide["id"] in slide_ids:
                raise ValueError(f"Duplicate slide id {slide['id']} in {data['id']}")
            slide_ids.add(slide["id"])
            for key in SLIDE_ARTIFACTS:
                if key in ("target", "render") or slide.get(key):
                    local_file(slide.get(key), manifest.parent, manifest.parent)
            if any(slide.get(key) for key in ("semantic", "measurement", "measurement_overlay")):
                semantic = read_json(local_file(slide.get("semantic"), manifest.parent, manifest.parent))
                measurement = read_json(local_file(slide.get("measurement"), manifest.parent, manifest.parent))
                local_file(slide.get("measurement_overlay"), manifest.parent, manifest.parent)
                expected_ids = [item["id"] for item in semantic.get("entities", [])]
                measured_ids = [item["id"] for item in measurement.get("entities", [])]
                if not expected_ids or len(set(expected_ids)) != len(expected_ids) or sorted(expected_ids) != sorted(measured_ids):
                    raise ValueError("Per-slide interpretation and measurement must cover the same elements")
                source_hash = semantic.get("provenance", {}).get("source_sha256")
                if source_hash and source_hash != sha256(local_file(slide["target"], manifest.parent, manifest.parent)):
                    raise ValueError("Per-slide interpretation belongs to a different design")
            if slide.get("objects"):
                object_file = local_file(slide["objects"], manifest.parent, manifest.parent)
                render_file = local_file(slide["render"], manifest.parent, manifest.parent)
                validate_object_binding(read_json(object_file), slide, page,
                                        downloads["pptx"], pptx_hash, sha256(render_file))
        process = data.get("process")
        if not isinstance(process, list) or not process:
            raise ValueError(f"At least one retained process artifact is required in {data['id']}")
        for step in process:
            if not isinstance(step, dict) or not step.get("title") or not step.get("description"):
                raise ValueError(f"Process artifacts need a title and description in {data['id']}")
            local_file(step.get("artifact"), manifest.parent, manifest.parent)
        for source in manifest.parent.rglob("*"):
            if source.is_symlink():
                raise ValueError(f"Portable examples must not contain symlinks: {source.relative_to(ROOT)}")
        manifests.append(manifest)
    validate_site_model(index, manifests)
    return manifests


def build(output: Path, manifests: list[Path]) -> dict:
    output = output.expanduser().resolve()
    if output.exists():
        raise ValueError(f"Output already exists. Choose a new directory: {output}")
    for source in (SITE, *(manifest.parent for manifest in manifests)):
        if output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError("The output must not overlap a source directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".slidepoise-site-", dir=output.parent) as temporary:
        staging = Path(temporary) / "site"
        site_target = staging / "docs" / "site"
        site_target.mkdir(parents=True)
        for name in STATIC_FILES:
            shutil.copy2(SITE / name, site_target / name)
        # New page markup must request the matching stylesheet and entry script,
        # even when a returning visitor has cached an earlier deployment.
        entrypoint = site_target / "index.html"
        html = entrypoint.read_text(encoding="utf-8")
        for name in STATIC_FILES:
            if Path(name).suffix in {".css", ".mjs"}:
                version = sha256(site_target / name)[:16]
                for attribute in ("href", "src"):
                    html = html.replace(f'{attribute}="{name}"', f'{attribute}="{name}?v={version}"')
        entrypoint.write_text(html, encoding="utf-8")
        if (SITE / "assets").is_dir():
            shutil.copytree(SITE / "assets", site_target / "assets")
        if (SITE / "console-demo").is_dir():
            shutil.copytree(SITE / "console-demo", site_target / "console-demo")
        for manifest in manifests:
            shutil.copytree(
                manifest.parent,
                staging / manifest.parent.relative_to(ROOT),
                ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"),
            )
        shutil.copy2(ROOT / "LICENSE", staging / "LICENSE")
        (staging / "index.html").write_text(
            '<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>SlidePoise showcase</title>'
            '<style>html{background:#faf9f6}</style>'
            '<script>location.replace("docs/site/"+location.search+location.hash)</script>'
            '<noscript><meta http-equiv="refresh" content="0; url=docs/site/">'
            '<a href="docs/site/">Open SlidePoise</a></noscript></html>\n',
            encoding="utf-8",
        )
        inventory = []
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                inventory.append({
                    "path": path.relative_to(staging).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                })
        (staging / "asset-inventory.json").write_text(
            json.dumps({"schema_version": 1, "files": inventory}, indent=2) + "\n",
            encoding="utf-8",
        )
        staging.replace(output)
    return {"output": str(output), "files": len(inventory), "bytes": sum(item["bytes"] for item in inventory)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--check", action="store_true", help="Validate manifests and referenced files")
    destination.add_argument("--output", type=Path, help="Create a new portable site directory")
    args = parser.parse_args()
    try:
        manifests = validate()
        result = {"presentations": len(manifests), "manifests": [str(path.relative_to(ROOT)) for path in manifests]}
        if args.output:
            result.update(build(args.output, manifests))
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError, TypeError) as error:
        print(f"Showcase validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
