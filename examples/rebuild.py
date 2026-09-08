#!/usr/bin/env python3
"""Rebuild a curated example through the installed reconstruction boundary.

The accepted designs and host-authored semantic maps are frozen inputs. This
command makes no design decisions and never calls an alternate deck builder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPTS = REPOSITORY / "slidepoise/scripts"


def run(script: str, *arguments: object, env: dict[str, str] | None = None) -> None:
    subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, arguments)], check=True, env=env)


def rebuild(example: Path, output: Path, *, preview: bool = True) -> None:
    example, output = example.resolve(), output.resolve()
    authoring = example / "run"
    outline = json.loads((authoring / "work/deck-outline.json").read_text(encoding="utf-8"))
    active = [slide for slide in outline["slides"] if slide.get("disposition", "active") == "active"]
    if not active:
        raise ValueError("The example has no active slides")
    if output.exists():
        raise FileExistsError(f"Choose a new output directory to preserve earlier evidence: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".slidepoise-rebuild-", dir=output.parent) as temporary:
        stage = Path(temporary)
        # An empty isolated home makes the resolver use the checkout's Library Sets.
        # A contributor's installed customization must not alter the curated example.
        environment = {**os.environ, "SLIDEPOISE_HOME": str(stage / "isolated-home")}
        work = stage / "work"
        work.mkdir()
        # Do not reuse an author's installation snapshot on a different machine.
        overrides = stage / "session-overrides.json"
        shutil.copy2(authoring / "session-overrides.json", overrides)
        config = work / "resolved-config.json"
        run("resolve_config.py", "--base", REPOSITORY / "framework/defaults/slidepoise-config.json",
            "--profiles-root", REPOSITORY / "profiles", "--session", overrides, "--output", config, env=environment)
        entries = []
        inputs = []
        shared_design = authoring / "work/deck-design.json"
        if shared_design.is_file():
            shutil.copy2(shared_design, work / "deck-design.json")
            inputs.append({"path": "run/work/deck-design.json",
                           "sha256": hashlib.sha256(shared_design.read_bytes()).hexdigest()})
        for slide in active:
            identifier = slide["slide_id"]
            source = (authoring / "slides" / identifier / "work").resolve()
            source.relative_to((authoring / "slides").resolve())
            destination = stage / "slides" / identifier / "work"
            destination.mkdir(parents=True)
            handoff = json.loads((source / "reconstruction-handoff.json").read_text(encoding="utf-8"))
            design_binding = handoff.get("deck_design_source")
            if design_binding is not None:
                if not isinstance(design_binding, dict) or not isinstance(design_binding.get("path"), str):
                    raise ValueError(f"Malformed deck design binding for {identifier}")
                relative_design = Path(design_binding["path"])
                # Retain the exact authored handoff. Its reference must resolve
                # to the copied shared decision after the temporary tree moves.
                if (relative_design.is_absolute()
                        or (source / relative_design).resolve() != shared_design.resolve()
                        or (destination / relative_design).resolve() != (work / "deck-design.json").resolve()):
                    raise ValueError(f"Deck design binding must resolve to run/work/deck-design.json for {identifier}")
                if not shared_design.is_file() or hashlib.sha256(shared_design.read_bytes()).hexdigest() != design_binding.get("sha256"):
                    raise ValueError(f"Stale or missing shared deck design for {identifier}")
            for name in ("accepted-slide.png", "semantic-map.json", "reconstruction-handoff.json"):
                shutil.copy2(source / name, destination / name)
                inputs.append({"path": (Path("run/slides") / identifier / "work" / name).as_posix(),
                               "sha256": hashlib.sha256((destination / name).read_bytes()).hexdigest()})
            semantic = json.loads((source / "semantic-map.json").read_text(encoding="utf-8"))
            for entity in semantic.get("entities", []):
                if (entity.get("raster_decision") or {}).get("action") == "reuse_original":
                    continue
                asset_reference = entity.get("raster_source_override")
                if not asset_reference:
                    continue
                relative_asset = Path(asset_reference)
                if relative_asset.is_absolute():
                    raise ValueError(f"Example artwork must use a relative path for {identifier}/{entity['id']}")
                asset = (source / relative_asset).resolve()
                asset.relative_to(authoring)
                copied_asset = (destination / relative_asset).resolve()
                copied_asset.relative_to(stage)
                copied_asset.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(asset, copied_asset)
                inputs.append({"path": asset.relative_to(example).as_posix(),
                               "sha256": hashlib.sha256(asset.read_bytes()).hexdigest()})
            reconstruction = destination / "reconstruction"
            run("slidepoise_runtime.py", "reconstruct-slide", "--image", destination / "accepted-slide.png",
                "--semantic-map", destination / "semantic-map.json", "--upstream-handoff", destination / "reconstruction-handoff.json",
                "--config", config, "--slide-id", identifier, "--output-dir", reconstruction, "--sam", "never", env=environment)
            entries.append({"slide_id": identifier, "scene": str(Path("../slides") / identifier / "work/reconstruction/constructor-scene.json")})
        manifest = work / "deck-scenes.json"
        manifest.write_text(json.dumps({"title": outline["title"], "language": "en-US", "slides": entries}, indent=2) + "\n", encoding="utf-8")
        shutil.copy2(authoring / "work/deck-outline.json", work / "deck-outline.json")
        deliverables = stage / "deliverables"
        deliverables.mkdir()
        run("slidepoise_runtime.py", "render-deck", "--manifest", manifest, "--output", deliverables / "presentation.pptx", env=environment)
        if preview:
            run("slidepoise_runtime.py", "render-deck-preview", "--pptx", deliverables / "presentation.pptx", "--output-dir", stage / "preview", env=environment)
        # Package portable scenes before publishing. Evidence retains exact authorship.
        run("slidepoise_runtime.py", "bundle-deck", "--manifest", manifest, "--output-dir", stage / "bundle", env=environment)
        receipt = {"schema_version": "1.0", "example": example.name,
                   "slide_ids": [entry["slide_id"] for entry in entries], "input_files": inputs,
                   "session_overrides_sha256": hashlib.sha256(overrides.read_bytes()).hexdigest(),
                   "measurement": "OpenCV", "library_source": "repository",
                   "portable_manifest": "bundle/deck-scenes.json", "presentation": "deliverables/presentation.pptx"}
        (stage / "rebuild.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        # Preserve diagnostic paths as provenance. Render the portable bundle for any
        # further edit after publication, since temporary authoring paths have moved.
        if output.exists():
            raise FileExistsError(f"Output appeared during the rebuild. Existing files are preserved. {output}")
        stage.rename(output)
    print(f"Rebuilt example at {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", type=Path, help="Example directory containing run/work/deck-outline.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--no-preview", action="store_true", help="Build editable PowerPoint without requiring LibreOffice")
    args = parser.parse_args()
    rebuild(args.example.resolve(), args.output_dir.resolve(), preview=not args.no_preview)


if __name__ == "__main__":
    main()
