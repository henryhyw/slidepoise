"""Check actual rebuilt and relocated native output against the reviewed deck."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageChops

RUN = Path(__file__).resolve().parents[1]
REPO = RUN.parents[2]
REBUILT = REPO / "output/product-qa-v4/editorial-full-rebuild"
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

comparisons = []
for index in range(1, 6):
    paths = [RUN / "preview" / f"slide-{index:03}.png", REBUILT / "preview" / f"slide-{index:03}.png", REBUILT / "portable-preview" / f"slide-{index:03}.png"]
    images = [Image.open(p).convert("RGB") for p in paths]
    same = all(images[0].size == im.size and ImageChops.difference(images[0], im).getbbox() is None for im in images[1:])
    assert same
    comparisons.append({"page": index, "reference_sha256": sha(paths[0]), "rebuilt_sha256": sha(paths[1]), "portable_sha256": sha(paths[2]), "dimensions": images[0].size, "pixels_identical": same})

with zipfile.ZipFile(RUN / "deliverables/presentation.pptx") as original, zipfile.ZipFile(REBUILT / "deliverables/presentation.pptx") as current, zipfile.ZipFile(REBUILT / "deliverables/portable.pptx") as portable:
    parts = [n for n in original.namelist() if n.endswith(".xml") and n.startswith(("ppt/slides/slide", "ppt/slideLayouts/slideLayout", "ppt/slideMasters/slideMaster"))]
    native = [{"part": n, "rebuild_identical": original.read(n) == current.read(n), "portable_identical": original.read(n) == portable.read(n)} for n in parts]
    assert all(item["rebuild_identical"] and item["portable_identical"] for item in native)
    notes = [{"part": n, "raw_identical": original.read(n) == current.read(n)} for n in original.namelist() if n.startswith("ppt/notesSlides/notesSlide") and n.endswith(".xml")]

missing_temporary_sources = []
design_bindings = []
for path in sorted(REBUILT.glob("slides/*/work/reconstruction/constructor-scene.json")):
    scene = json.loads(path.read_text())
    for obj in scene["objects"]:
        if obj["kind"] == "image":
            source = Path(obj["source_path"])
            missing_temporary_sources.append(not source.exists())
    handoff = path.parents[1] / "reconstruction-handoff.json"
    binding = json.loads(handoff.read_text())["deck_design_source"]
    resolved = (handoff.parent / binding["path"]).resolve()
    valid = resolved.is_file() and sha(resolved) == binding["sha256"]
    assert valid
    design_bindings.append({"slide_id": scene["slide_id"], "resolves_after_move": valid, "sha256": binding["sha256"]})
assert all(missing_temporary_sources) and len(missing_temporary_sources) == 8
record = {
    "schema_version": "1.0", "method": "examples/rebuild.py re-resolved repository configuration in an isolated home, measured the frozen targets with OpenCV, compiled native scenes and rendered the complete deck. The portable bundle was then rendered again after the original temporary crop paths were gone. All actual previews used120 DPI.",
    "source_pptx_sha256": sha(RUN / "deliverables/presentation.pptx"),
    "rebuilt_pptx_sha256": sha(REBUILT / "deliverables/presentation.pptx"),
    "portable_pptx_sha256": sha(REBUILT / "deliverables/portable.pptx"),
    "render_comparisons": comparisons, "native_xml_comparisons": native,
    "notes_xml_comparisons": notes,
    "notes_explanation": "No audience speaker_notes are authored in this essay. Historical source-reference paths change correctly with the rebuilt workspace.",
    "original_temporary_raster_sources_missing": len(missing_temporary_sources),
    "shared_design_handoff_bindings": design_bindings,
    "frozen_input_bindings": json.loads((REBUILT / "rebuild.json").read_text())["input_files"],
    "preview_environment_scope": "Recorded macOS LibreOffice and installed fonts. This establishes reproduction of frozen reconstruction inputs, not deterministic image generation."
}
(RUN / "work/rebuild-verification.json").write_text(json.dumps(record, indent=2) + "\n")
(REBUILT / "verification.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"all_pages_pixel_identical": True, "native_parts_identical": len(native), "portable_render_without_original_crops": True, "shared_design_bindings": len(design_bindings)}))
