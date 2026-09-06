"""Stage the inspected Editorial revision and atomically replace the local case."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

RUN = Path(__file__).resolve().parents[1]
REPO = RUN.parents[2]
CASE = RUN.parent / "personal-v2-case"
LIVE = REPO / "examples/personal-thinking-system"
ARCHIVE = RUN.parent / "personal-v1-at-replacement"
assert CASE.is_dir() and not ARCHIVE.exists()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def bind(path):
    return {"path": str(path.relative_to(CASE)), "sha256": sha(path)}

shutil.copytree(RUN, CASE / "run", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
for name in ["assets", "deliverables"]:
    (CASE / name).mkdir(exist_ok=True)
shutil.copytree(RUN / "preview", CASE / "preview", dirs_exist_ok=True)
shutil.copy2(RUN / "deliverables/presentation.pptx", CASE / "deliverables/presentation.pptx")
shutil.copy2(RUN / "preview/presentation.pdf", CASE / "deliverables/presentation.pdf")
shutil.copy2(RUN / "preview/contact-sheet.png", CASE / "assets/contact-sheet.png")
manifest = json.loads((LIVE / "showcase.json").read_text())
manifest["revision"] = 2
manifest["downloads"] = {"pptx": "deliverables/presentation.pptx"}
manifest["canvas"] = {"full_slide_px": [1600, 900], "content_region_px": [0, 0, 1600, 900]}
for index, slide in enumerate(manifest["slides"], 1):
    page = RUN / "slides" / slide["id"]
    for source, suffix in [(page / "work/accepted-slide.png", "target"), (RUN / "preview" / f"slide-{index:03}.png", "render"), (page / "deliverables/semantic-explanation.png", "semantic")]:
        shutil.copy2(source, CASE / "assets" / f"{slide['id']}-{suffix}.png")
    shutil.copy2(page / "work/semantic-explanation.json", CASE / "assets" / f"{slide['id']}-semantic.json")
manifest["process"][-1].update(title="Keep the series coherent", description="The Agent compares the actual pages and applies one Field Notes identity. The review records the shared role, its page aliases and the preserved artwork.")
(CASE / "showcase.json").write_text(json.dumps(manifest, indent=2) + "\n")
(CASE / "README.md").write_text("""# A second thinking system

A five-page Editorial sample about working with AI while keeping questions, connections and judgement visible. Its first-person voice belongs to the authored essay.

The presentation combines editable typography and rules with preserved photographic collage. The native output has 46 text boxes, nine shapes and seven editable freeforms. Eight regional images retain the generated notebook, hands, paper and depicted marks.

## Shared identity, individual pages

The second revision keeps the original artwork, body copy and distinctive page compositions. It calibrates the repeated `FIELD NOTES / 01` through `05` markers to Andale Mono regular at 12 pt, with zero character spacing, dark ink and one lower-left baseline. The cover-only short rule and essay descriptor move with its marker to preserve their relationship.

The Agent discovered that the same publication role appeared under different local entity names. `run/work/deck-design.json` records the shared treatment and aliases. Every reconstruction handoff binds that decision by hash, while the actual semantic styles implement it. The role declaration does not choose or apply typography automatically.

`run/work/folio-calibration/folio-comparison.png` shows the actual native before/after result. Same-DPI comparison found no changed pixels outside the authorized series-marker regions and cover companions. Native media payloads and every non-folio text object's content and typography stayed unchanged.

## Creative source and reconstruction

The original generated targets are retained honestly as historical full-slide designs. No new image call was made for this native calibration. Their old folio placements remain visible in target comparisons. New presentations follow the current body-only generation and inherited-frame policy.

The Agent retained the original collage crops, revised the semantic inputs and ran the packaged OpenCV measurement, contract, compiler and renderer again. Every page has current measurements, actual PowerPoint renders and exact-file visual reviews. Available native font outlines differ from the generated lettering. Photograph texture and intrinsic depicted marks remain raster.

## Reproduce and inspect

Run `examples/rebuild.py` from the repository to repeat native reconstruction from the retained creative inputs. The second revision was rebuilt in an isolated home with repository resources. All five actual 120 DPI previews were pixel-identical, and seven slide, layout and master XML parts matched. The portable bundle also rendered identically after the original temporary crop paths were removed. These results describe the recorded macOS LibreOffice and font environment.

`run/bundle/deck-scenes.json` is the portable scene entry point. `run/work/rebuild-verification.json` records the current checks. The source ZIP includes that bundle and the complete authoring evidence. The project page offers one PowerPoint download action. PDF and source files remain available in the repository.

The previous local example was retained at `output/showcase-revisions/personal-v1-at-replacement`. No external deployment is implied.
""")
subprocess.run([sys.executable, str(REPO / "docs/site/extract_objects.py"), "--manifest", str(CASE / "showcase.json")], check=True)
with zipfile.ZipFile(CASE / "deliverables/source-bundle.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted((CASE / "run").rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(CASE))
    archive.write(CASE / "README.md", "README.md")
record = {"schema_version": "1.0", "revision": 2, "publication": "local example replacement, not external deployment", "source_pptx": bind(CASE / "deliverables/presentation.pptx"), "source_archive": bind(CASE / "deliverables/source-bundle.zip"), "deck_design": bind(CASE / "run/work/deck-design.json"), "rebuild_evidence": bind(CASE / "run/work/rebuild-verification.json"), "calibration_evidence": bind(CASE / "run/work/folio-calibration/verification.json"), "public_download": "PowerPoint only", "preserved_previous_case": str(ARCHIVE), "source_bindings": [bind(CASE / "assets" / f"{s['id']}-{kind}{extension}") for s in manifest["slides"] for kind, extension in [("target", ".png"), ("render", ".png"), ("semantic", ".json"), ("objects", ".json")]]}
(CASE / "publication.json").write_text(json.dumps(record, indent=2) + "\n")
for slide in manifest["slides"]:
    for key in ["target", "render", "evidence", "scene", "objects"]:
        assert (CASE / slide[key]).is_file(), slide[key]
    assert json.loads((CASE / "run/slides" / slide["id"] / "work/release-evidence.json").read_text())["blocking_facts"] == []
with zipfile.ZipFile(CASE / "deliverables/source-bundle.zip") as archive:
    assert archive.testzip() is None
LIVE.rename(ARCHIVE)
try:
    CASE.rename(LIVE)
except BaseException:
    ARCHIVE.rename(LIVE)
    raise
print(json.dumps({"local_case": str(LIVE), "previous_case": str(ARCHIVE), "pptx_sha256": record["source_pptx"]["sha256"], "source_archive_sha256": record["source_archive"]["sha256"]}, indent=2))
