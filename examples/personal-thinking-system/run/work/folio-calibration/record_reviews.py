"""Persist observations from the host's completed full-page visual review."""
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

RUN = Path(__file__).resolve().parents[2]
QA = Path(__file__).parent

def write(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")

def binding(path, relative_to):
    return {"path": os.path.relpath(path, relative_to), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

page_observations = [
    "The large three-line Bodoni statement and hand/staircase collage keep their original balance. The series label, short rule and essay descriptor now share a lower baseline, with clear separation from the subtitle and artwork.",
    "The enlarged regular monospaced folio reads cleanly below the eye collage. The two italic reflective questions, their nearby rule and the closing sentence retain their original hierarchy and positions.",
    "The folio sits below the three collage columns with clear breathing room. The subtitle and captions keep their existing typewriter voice, while the folio now has the same physical size and baseline as its peers.",
    "The former tiny bold sans folio is now the shared regular archive label. The four numbered record rows, their rules, the notebook photograph and the tall collage remain unchanged and clearly separated from it.",
    "The closing folio loses the former bold wide-spaced treatment and aligns with the first four pages. The large serif conclusion, three closing sentences and hand/thread collage retain the original composition."
]
all_artifacts = []
counts = Counter()
for index, page in enumerate(sorted((RUN / "slides").iterdir())):
    work = page / "work"
    deliver = page / "deliverables"
    scene = json.loads((work / "reconstruction/constructor-scene.json").read_text())
    counts.update(o["kind"] for o in scene["objects"])
    common = {"reviewer": "host_agent_visual_reasoning", "decision": "accepted", "material_issues": [], "review_environment": "Actual LibreOffice rendering on macOS, installed system fonts, 120 DPI. Five full-resolution pages and both contact sheets inspected.", "user_checkpoint": "The user explicitly requested consistent Field Notes typography across all five existing pages while retaining their artwork and compositions."}
    generation = dict(common, stage="generation", reasoning_summary="The existing generated target remains accepted as historical artwork and substantive composition for this authorized native calibration. No new image-generation call is claimed.", observations=["This is a retained legacy full-slide image, including its original page label. Its hash and original generation evidence are preserved.", "The folio's original inconsistent style and location are intentionally revised through the explicit shared deck role. The accepted image remains the source of all other composition and raster regions."], reviewed_artifacts=[binding(work / "accepted-slide.png", work), binding(QA / "originals/slides" / page.name / "work/generation-review.json", work)])
    generation["candidate_index"] = json.loads((QA / "originals/slides" / page.name / "work/generation-review.json").read_text())["candidate_index"]
    measure_paths = [work / "accepted-slide.png", work / "semantic-map.json", work / "reconstruction/measurement/slide_entities.json", work / "reconstruction/measurement/debug_overlay.png"]
    measurement = dict(common, stage="measurement", reasoning_summary="The inspected overlay keeps source ink evidence separate from the revised native folio allocation.", observations=["Grey search windows retain the full original text ink. The new orange folio allocation is the same on all five pages and does not overlap substantive artwork or body text.", "The raster boundaries remain those of the original accepted target. No collage region was segmented differently or replaced.", "The deliberate displacement between source folio ink and native allocation records the user's revision. It is not measurement error."], reviewed_artifacts=[binding(p, work) for p in measure_paths])
    paths = measure_paths + [work / "reconstruction-handoff.json", RUN / "work/deck-design.json", work / "reconstruction/reconstruction-contract.json", work / "reconstruction/constructor-scene.json", deliver / "slide.pptx", deliver / "render.png", deliver / "comparison.png", deliver / "difference.png"]
    reconstruction = dict(common, stage="reconstruction", reasoning_summary="The actual native render implements the common publication identity while preserving the page's original substantive composition.", observations=[page_observations[index], "The native folio uses Andale Mono regular12pt, zero tracking, dark ink and the common lower-left allocation. All words remain editable.", "Same-DPI actual old/new rendering shows no pixel change outside the authorized folio assembly. Native media payloads and non-folio text typography are unchanged."], remaining_fidelity_limits=["The historical generated lettering and available native fonts have different glyph outlines. This revision preserves the existing approved native body interpretation.", "Photographic collage and intrinsic depicted lettering remain raster. Native paper backgrounds retain sampled flat tones.", "Legacy full-slide generation history is retained honestly. No claim is made that the old images were generated using the current body-only frame policy."], reviewed_artifacts=[binding(p, work) for p in paths])
    write(work / "generation-review.json", generation)
    write(work / "measurement-review.json", measurement)
    write(work / "reconstruction-review.json", reconstruction)
    all_artifacts.extend([binding(deliver / "render.png", RUN / "work"), binding(work / "reconstruction/constructor-scene.json", RUN / "work")])

deck_artifacts = [RUN / "deliverables/presentation.pptx", RUN / "preview/presentation.pdf", RUN / "preview/contact-sheet.png", RUN / "work/deck-design.json", QA / "folio-comparison.png", QA / "verification.json", QA / "native-text-audit.json"]
review = {"reviewer": "host_agent_visual_reasoning", "stage": "assembled_deck", "decision": "accepted", "material_issues": [], "review_scope": "Inspected all five actual full-resolution page renders, the old/new contact sheets, five measurement overlays and the enlarged folio comparison. Native object facts and actual pixel differences corroborate the reviewed scope.", "observations": ["All five Field Notes part markers now form one publication identity with the same typeface, physical size, regular weight, tracking, dark ink and lower-left baseline.", "The five distinct compositions remain an editorial essay sequence. Large statements, body copy, record rows and photographic collages keep their intended differences.", "The cover-only descriptor and short linking rule retain their relationship to the series marker. They are recorded as a specific exception, not a new recurring motif.", "A renewed cross-page scan found no further accidental repeat-role drift within this bounded revision. Large title sizes and content-specific captions are retained as intentional composition differences."], "native_object_counts": dict(counts), "reviewed_artifacts": all_artifacts + [binding(p, RUN / "work") for p in deck_artifacts], "publication_status": "Prepared in an isolated authoring run. Root publication to the live example is pending."}
write(RUN / "work/deck-review.json", review)
write(QA / "visual-review.json", {**review, "reviewed_artifacts": [binding(p, QA) for p in deck_artifacts]})
