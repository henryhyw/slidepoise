"""Collect file and rendering facts for the host-reviewed folio revision."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image, ImageChops

RUN = Path(__file__).resolve().parents[2]
QA = Path(__file__).parent
LIVE = RUN.parents[2] / "examples/personal-thinking-system"
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main", "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def binding(path):
    return {"path": str(path.relative_to(RUN)), "sha256": sha(path)}

def native_facts(archive, index):
    root = ET.fromstring(archive.read(f"ppt/slides/slide{index}.xml"))
    result = {}
    for shape in root.findall(".//p:sp", NS):
        name = shape.find("p:nvSpPr/p:cNvPr", NS).get("name")
        text = "\n".join("".join(p.itertext()) for p in shape.findall("p:txBody/a:p", NS))
        # Inspect text nodes explicitly so formatting attributes never become content.
        text = "\n".join("".join(t.text or "" for t in p.findall(".//a:t", NS)) for p in shape.findall("p:txBody/a:p", NS))
        runs = []
        for props in shape.findall(".//a:rPr", NS):
            font = props.find("a:latin", NS)
            color = props.find("a:solidFill/a:srgbClr", NS)
            runs.append({"family": font.get("typeface") if font is not None else None, "size_pt": int(props.get("sz")) / 100, "bold": props.get("b", "0"), "italic": props.get("i", "0"), "spacing_pt": int(props.get("spc", "0")) / 100, "color": color.get("val") if color is not None else None})
        result[name] = {"text": text, "runs": runs}
    return result

records = []
with zipfile.ZipFile(QA / "originals/deliverables/presentation.pptx") as original, zipfile.ZipFile(RUN / "deliverables/presentation.pptx") as current:
    original_media = sorted(hashlib.sha256(original.read(n)).hexdigest() for n in original.namelist() if n.startswith("ppt/media/"))
    current_media = sorted(hashlib.sha256(current.read(n)).hexdigest() for n in current.namelist() if n.startswith("ppt/media/"))
    assert current_media == original_media, "Native media bytes changed"
    for index, page in enumerate(sorted((RUN / "slides").iterdir()), 1):
        old_scene = json.loads((QA / "originals/slides" / page.name / "work/reconstruction/constructor-scene.json").read_text())
        scene = json.loads((page / "work/reconstruction/constructor-scene.json").read_text())
        role_ids = {"field-note" if index < 4 else "folio"}
        if index == 1:
            role_ids |= {"essay-label", "footer-rule"}
        old_image = Image.open(QA / "original-preview" / f"slide-{index:03}.png").convert("RGB")
        image = Image.open(RUN / "preview" / f"slide-{index:03}.png").convert("RGB")
        assert old_image.size == image.size
        difference = ImageChops.difference(old_image, image)
        changed = np.any(np.asarray(difference) != 0, axis=2)
        allowed = np.zeros_like(changed)
        areas = []
        for authored in (old_scene, scene):
            for obj in authored["objects"]:
                if obj["id"] in role_ids:
                    x, y, w, h = obj["bbox_px"]
                    rect = [max(0, x - 5), max(0, y - 5), min(image.width, x + w + 5), min(image.height, y + h + 5)]
                    allowed[rect[1]:rect[3], rect[0]:rect[2]] = True
                    areas.append(rect)
        outside = int(np.count_nonzero(changed & ~allowed))
        assert outside == 0, "Unexpected visible change outside the authorized folio assembly"
        before = native_facts(original, index)
        after = native_facts(current, index)
        unchanged = [name for name in after if name not in role_ids]
        assert all(before[name] == after[name] for name in unchanged), "Non-folio text or native typography changed"
        name = "field-note" if index < 4 else "folio"
        assert after[name]["runs"] == [{"family": "Andale Mono", "size_pt": 12, "bold": "0", "italic": "0", "spacing_pt": 0, "color": "242321"}]
        assert (LIVE / "run/slides" / page.name / "work/accepted-slide.png").read_bytes() == (page / "work/accepted-slide.png").read_bytes()
        individual = Image.open(page / "deliverables/render.png").convert("RGB")
        assert ImageChops.difference(image, individual).getbbox() is None
        previous_revision = Image.open(QA / "iteration-01-role-record/preview" / f"slide-{index:03}.png").convert("RGB")
        assert ImageChops.difference(image, previous_revision).getbbox() is None
        difference.save(QA / f"{page.name}-actual-difference.png")
        records.append({"slide_id": page.name, "folio_before": before[name], "folio_after": after[name], "changed_pixel_bbox": difference.getbbox(), "authorized_native_regions_with_5px_antialias_padding": areas, "changed_pixels_outside_authorized_regions": outside, "unchanged_nonfolio_native_text_objects": len(unchanged), "individual_and_assembled_render_identical": True, "canonical_metadata_update_render_identical": True, "accepted_target_unchanged": True, "reviewed_render": binding(page / "deliverables/render.png"), "compiled_scene": binding(page / "work/reconstruction/constructor-scene.json")})

retained = json.loads((QA / "original-bindings.json").read_text())
source_intact = all(sha(LIVE / "run" / item["path"]) == item["sha256"] for item in retained["files"])
assert source_intact
result = {"evidence_type": "objective_revision_facts", "visual_acceptance_owner": "host_agent", "source_deck": binding(QA / "originals/deliverables/presentation.pptx"), "revised_deck": binding(RUN / "deliverables/presentation.pptx"), "deck_design": binding(RUN / "work/deck-design.json"), "original_live_source_files_unchanged_before_publication": source_intact, "native_media_payloads_byte_identical": True, "native_media_count": len(current_media), "slides": records}
(QA / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"slides": len(records), "unchanged_native_media": len(current_media), "pixels_changed_outside_authorized_roles": sum(p["changed_pixels_outside_authorized_regions"] for p in records)}))
