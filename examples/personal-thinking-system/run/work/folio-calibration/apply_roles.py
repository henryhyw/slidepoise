"""Apply the host's reviewed folio decision to semantic inputs, never to PPTX."""
import json
import hashlib
from pathlib import Path

RUN = Path(__file__).resolve().parents[2]
ORIGINALS = Path(__file__).parent / "originals"
PAGES = ["s01-opening", "s02-question", "s03-practice", "s04-trace", "s05-close"]

def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")

roles = {
    "schema_version": "1.0",
    "author": "host_agent_visual_reasoning",
    "purpose": "User-authorized calibration of an existing presentation's recurring publication identity.",
    "source_canvas_px": [1672, 941],
    "native_canvas_px": [1600, 900],
    "roles": [{
        "id": "publication_folio",
        "meaning": "The Field Notes series label and current essay part number on every page.",
        "page_aliases": [{"slide_id": p, "entity_id": "field-note" if i < 3 else "folio", "previous_typography_group": "page-index" if i < 3 else "emphasis_label"} for i, p in enumerate(PAGES)],
        "chosen_style": {
            "font_family": "Andale Mono", "font_weight": "regular", "native_font_size_pt": 12,
            "target_font_size_px": 21, "color": "#242321", "char_spacing_px": 0,
            "italic": False, "casing": "FIELD NOTES / NN", "align": "left", "valign": "top",
            "line_spacing": 1, "bbox_hint": [90, 868, 300, 38], "rule": "No repeated folio rule"
        },
        "reasoning": "The monospaced archive label already used on the first three pages provides a coherent identity within the paper-collage art direction. A 12 pt native setting is legible at presentation size. One lower-left allocation, regular weight, normal tracking and dark ink make the five part numbers read as a series.",
        "exceptions": [{"slide_id": "s01-opening", "entity_ids": ["essay-label", "footer-rule"], "reason": "The cover-only essay descriptor and short linking rule remain unique companion elements. They move by the same 54 source pixels as the folio to preserve their original baseline relationship. Their typography and horizontal placement remain unchanged."}]
    }],
    "other_recurring_functions_reviewed": [
        {"function": "Main essay statements", "decision": "Keep observed Bodoni 72 lettering, size, tracking and composition. Their hierarchy and line structure are intentionally page-specific."},
        {"function": "Explanatory copy", "decision": "Keep the existing Arial or Andale Mono roles. Reflective questions, chapter captions and archival ledger prompts serve distinct local reading functions."},
        {"function": "Rules and record numbers", "decision": "Column dividers, ledger rules and numbered record rows are content structures on their own pages. They are not a recurring footer rule."},
        {"function": "Artwork and paper", "decision": "Retain every accepted regional raster, background tone, crop and native body allocation."}
    ],
    "generation_policy": "Reuse the existing accepted targets. This authorized native calibration does not claim the legacy generated folio placement or style is the new target. No image-generation call was made."
}
write(Path(__file__).parent / "role-discovery.json", roles)
role = roles["roles"][0]
design = {
    "schema_version": "1.0",
    "design_id": "editorial-field-notes-publication-identity-v2",
    "purpose": "The Agent reviewed five existing pages and applied the user's requested consistent Field Notes identity. Original generated targets and artwork remain historical source material. No new generation call was made.",
    "frame_source": "resolved-config.json#/design/frame",
    "repeated_roles": {
        "publication_folio": {
            "purpose": role["meaning"],
            "recognition_evidence": "The same FIELD NOTES publication identity and changing 01 to 05 part suffix appear at the bottom of all five actual pages, under two different local entity aliases. Original native fonts were Andale Mono regular12/10/9.5pt and Arial bold9.5/12pt, with wide tracking on the final page.",
            "chosen_style": {"font_family": "Andale Mono", "font_size_pt": 12, "font_weight": "regular", "italic": False, "character_spacing_pt": 0, "color": "#242321", "alignment": "left"},
            "placement_convention": "One lower-left native allocation at [86,830,287,36] on the 1600x900 scene. Semantic bbox [90,868,300,38] on the retained 1672x941 target, with target21px, produces native12pt. Uppercase FIELD NOTES / NN, top-anchored, normal leading. No repeated rule. Existing local folios are retained for this authorized revision of full-slide historical targets. Future generation follows the inherited-frame policy.",
            "page_aliases": [{"slide_id": p, "entity_ids": ["field-note" if i < 3 else "folio"], "typography_group": "publication-folio"} for i,p in enumerate(PAGES)],
            "exceptions": [{"exception_id": "cover-essay-companions", "slide_id": "s01-opening", "entity_ids": ["essay-label", "footer-rule"], "reason": role["exceptions"][0]["reason"], "review_focus": "The cover-only rule and essay caption preserve their baseline relationship beside the now shared folio. The folio itself follows the common treatment."}]
        }
    },
    "allowed_variations": [r["function"] + ". " + r["decision"] for r in roles["other_recurring_functions_reviewed"]],
    "reference_images": [],
    "cross_slide_review_focus": ["Compare all five actual folios for common face, weight, size, tracking, color and baseline. Inspect the full pages after reviewing the contact sheet.", "Confirm that every artwork crop and substantive text allocation remains unchanged. Review the cover-only caption relationship.", "Look for additional undeclared recurring functions. Body dividers and archive record numbers belong to their local content structures, while the title sizes preserve the approved individual compositions."]
}
write(RUN / "work/deck-design.json", design)
design_sha = hashlib.sha256((RUN / "work/deck-design.json").read_bytes()).hexdigest()

for i, page in enumerate(PAGES):
    w = RUN / "slides" / page / "work"
    old = ORIGINALS / "slides" / page / "work"
    semantic = json.loads((old / "semantic-map.json").read_text())
    handoff = json.loads((old / "reconstruction-handoff.json").read_text())
    entity = next(e for e in semantic["entities"] if e["id"] == ("field-note" if i < 3 else "folio"))
    entity.setdefault("search_bbox_hint", entity["bbox_hint"].copy())
    entity["bbox_hint"] = [90, 868, 300, 38]
    entity["role"] = "publication_folio"
    entity["typography_group"] = "publication-folio"
    entity["display_label"] = f"Field Notes series marker, part {i + 1:02d}"
    entity["style_hint"].update({"font_family": "Andale Mono", "font_weight": "regular", "target_font_size_px": 21, "observed_foreground_color": "#242321", "char_spacing_px": 0, "italic": False, "align": "left", "valign": "top", "line_spacing": 1, "style_authority": "host_reviewed_user_authorized_deck_role"})
    if i == 0:
        for e in semantic["entities"]:
            if e["id"] in ("essay-label", "footer-rule"):
                e.setdefault("search_bbox_hint", e["bbox_hint"].copy())
                e["bbox_hint"][1] += 54
    semantic.setdefault("provenance", {})["composition_policy"] = "accepted_artwork_and_body_preserved_with_user_authorized_publication_folio_calibration"
    semantic["provenance"]["revision"] = "Recurring publication_folio role and its cover-only companions follow work/deck-design.json. Source ink remains measured at the original target locations."
    handoff["deck_design_source"] = {"path": "../../../work/deck-design.json", "sha256": design_sha}
    handoff["recurring_role_bindings"] = [{"role_id": "publication_folio", "entity_ids": [entity["id"]], "typography_group": "publication-folio", "style_source": "repeated_roles.publication_folio.chosen_style", "exception_id": None, "application_note": "The Agent materialized the common native12pt role as Andale Mono regular target21px with zero tracking, common dark ink and a fixed logical allocation. Source-ink windows retain the original target locations. The binding itself does not apply the style."}]
    if i == 0:
        handoff["recurring_role_bindings"].append({"role_id": "publication_folio", "entity_ids": ["essay-label", "footer-rule"], "typography_group": "essay-label", "style_source": "repeated_roles.publication_folio.exceptions[cover-essay-companions]", "exception_id": "cover-essay-companions", "application_note": "Both cover-only companions move down54 source pixels with the series marker. Original caption typography, rule material and their horizontal positions remain unchanged."})
    handoff["revision_notes"] = ["The user requested one coherent Field Notes identity across all five pages. The Agent reviewed all original renders and calibrated this recurring role. Artwork and substantive content stay unchanged."]
    write(w / "semantic-map.json", semantic)
    write(w / "reconstruction-handoff.json", handoff)
