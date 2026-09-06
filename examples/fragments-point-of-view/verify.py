"""Check this case's file integrity and actual editable-object inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

CASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    return {p.relative_to(CASE).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size}
            for p in sorted(CASE.rglob("*")) if p.is_file() and p.name != "manifest.json"
            and "__pycache__" not in p.parts and p.name != ".DS_Store"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal", action="store_true", help="Create the initial inventory, refusing to replace one")
    args = parser.parse_args()
    manifest = CASE / "manifest.json"
    if args.seal:
        if manifest.exists():
            raise SystemExit("Inventory already exists. Refusing to replace it.")
        manifest.write_text(json.dumps({"purpose": "Curated artifact integrity only", "files": inventory()}, indent=2) + "\n")
    expected = json.loads(manifest.read_text())["files"]
    actual = inventory()
    differences = [name for name in expected.keys() | actual.keys() if expected.get(name) != actual.get(name)]
    if differences:
        raise SystemExit("Changed, missing, or extra files: " + ", ".join(sorted(differences)))
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
    with ZipFile(CASE / "deliverables/Fragments.pptx") as deck:
        slide = ET.fromstring(deck.read("ppt/slides/slide1.xml"))
        textboxes = [shape for shape in slide.findall(".//p:sp", ns) if shape.findall(".//a:t", ns)]
        curves = slide.findall(".//a:cubicBezTo", ns)
        pictures = slide.findall(".//p:pic", ns)
        assert len(textboxes) == 21, f"Text objects changed: {len(textboxes)}"
        assert len(curves) == 2, f"Curve commands changed: {len(curves)}"
        assert len(pictures) == 10, f"Image objects changed: {len(pictures)}"
        text = " ".join(node.text or "" for node in slide.findall(".//a:t", ns))
        assert "FIELD NOTES" not in text and "Clarity is a responsibility" not in text
        embedded = {hashlib.sha256(deck.read(name)).hexdigest() for name in deck.namelist() if name.startswith("ppt/media/")}
        originals = [p for p in (CASE / "assets/crops").glob("*.png") if "original" in p.name]
        assert len(originals) == 7
        assert all(sha(p) in embedded for p in originals), "An original crop is no longer embedded verbatim"
    scene = json.loads((CASE / "data/constructor-scene.json").read_text())
    for obj in scene["objects"]:
        if obj.get("source_path"):
            path = (CASE / obj["source_path"]).resolve()
            assert path.is_relative_to(CASE) and path.is_file(), "Unbundled scene image"
    print(json.dumps({"integrity_valid": True, "files": len(expected), "textboxes": len(textboxes), "cubic_paths": len(curves), "raster_objects": len(pictures), "original_crops_verified": len(originals), "scope": "Mechanical inventory, no visual acceptance claim"}, indent=2))


if __name__ == "__main__":
    main()
