"""Serialize host-observed allocations for the current 1920 by 960 accepted body."""
import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent
entities = []


def text(identifier, value, box, size, group, *, bold=False, color="#000000", family="Arial", role="body", search=None, leading=1.0, middle=False):
    entity = {"id": identifier, "display_label": value.replace("\n", " "), "kind": "text", "role": identifier,
              "text": value, "text_style_role": role, "typography_group": group, "bbox_hint": box,
              "search_bbox_hint": search or box, "geometry_policy": "agent_logical", "z": 20,
              "reconstruction_significance": "independent_object", "meaningful_visible": True,
              "style_hint": {"font_family": family, "font_weight": "bold" if bold else "regular",
                             "target_font_size_px": size, "alignment": "left", "line_spacing": leading,
                             "vertical_alignment": "middle" if middle else "top",
                             "observed_foreground_color": color, "style_authority": "agent_visual_observation"}}
    if color == "#FD5108":
        entity["style_token"] = "data_highlight" if role == "large_data_number" else "call_to_action"
    entities.append(entity)


def shape(identifier, box, fill):
    entities.append({"id": identifier, "display_label": identifier.replace("-", " "), "kind": "shape", "shape": "rectangle",
                     "role": "native_presentation_geometry", "bbox_hint": box, "geometry_policy": "agent_logical", "z": 1,
                     "meaningful_visible": True, "style_hint": {"fill": fill, "stroke": "none", "stroke_width_px": 0,
                     "style_authority": "agent_visual_observation"}})


text("headline", "Prove the research pilot before scaling AI", [45, 23, 1828, 85], 64, "claim-title", family="Georgia", role="slide_title", search=[43, 35, 1195, 70])
text("pilot-scope", "One practice. 15 consultants. 20 paired research tasks. A 12-week, $25k pilot.", [46, 118, 1827, 48], 32, "subtitle", role="subtitle", search=[45, 129, 1051, 32])
shape("introduction-rule", [47, 186, 1827, 2], "#AAAAAA")

text("capacity-heading", "RESEARCH CAPACITY IMPACT IF WE SCALE", [47, 229, 645, 43], 28, "section-headings", bold=True, role="heading_large", search=[47, 234, 535, 25])
text("argument-heading", "WHY THIS PILOT FIRST", [700, 229, 498, 43], 28, "section-headings", bold=True, role="heading_large", search=[699, 234, 283, 26])
text("gate-heading", "WEEK-12 SCALE GATE", [1223, 229, 649, 43], 28, "section-headings", bold=True, role="heading_large", search=[1222, 234, 277, 26])

for identifier, value, top, ink in [
    ("baseline", "10,800 h", 281, [46, 294, 275, 63]),
    ("capacity", "1,944 h", 461, [45, 475, 225, 60]),
    ("capacity-value", "$243k", 634, [44, 644, 208, 66]),
]:
    text(identifier, value, [46, top, 588, 86], 68, "display-data", bold=True, color="#FD5108", role="large_data_number", search=ink)

for identifier, value, top, ink in [
    ("baseline-label", "Annual research baseline", 354, [46, 364, 330, 27]),
    ("capacity-label", "Potential annual capacity", 532, [47, 541, 333, 27]),
    ("capacity-value-label", "Annual capacity equivalent", 703, [45, 714, 344, 27]),
]:
    text(identifier, value, [47, top, 604, 42], 28, "metric-labels", bold=True, role="heading_large", search=ink)

for identifier, value, top, ink in [
    ("baseline-formula", "900 engagements × 12 h", 392, [46, 399, 278, 29]),
    ("capacity-formula", "60% adoption × 30% time reduction", 570, [46, 578, 401, 29]),
    ("capacity-value-formula", "1,944 h × $125 per hour", 739, [47, 746, 271, 31]),
]:
    text(identifier, value, [47, top, 604, 42], 28, "metric-calculations", search=ink)
shape("metric-divider-1", [47, 448, 531, 1], "#B6B6B6")
shape("metric-divider-2", [47, 627, 531, 1], "#B6B6B6")

for number, top, detail_top, heading, detail in [
    ("01", 291, 334, "Focus a repeatable task", "Approved sources, frequent use\nand comparable inputs."),
    ("02", 472, 515, "Preserve expert review", "Verify every client claim\nbefore release."),
    ("03", 650, 692, "Fund against evidence", "Practice lead and CFO release\n$60k only after the week-12 gate."),
]:
    text("argument-number-"+number, number, [700, top-3, 70, 64], 48, "argument-numbers", bold=True, role="section_number", search=[698, top+8, 57, 53])
    text("argument-title-"+number, heading, [783, top, 438, 44], 28, "argument-titles", bold=True, role="heading_large", search=[782, top+9, 353, 34])
    text("argument-detail-"+number, detail, [783, detail_top-8, 445, 87], 28, "argument-details", leading=1.3, search=[782, detail_top+8, 442, 68])
shape("argument-divider-1", [701, 448, 439, 1], "#B6B6B6")
shape("argument-divider-2", [701, 627, 439, 1], "#B6B6B6")

rows = [["Measure", "Minimum to scale"], ["Cycle-time reduction", "25%"],
        ["Sampled cited claims verified", "95%"], ["Critical data exceptions", "0"],
        ["Weekly-active pilot users", "70% · at least 11 of 15"]]
cells = [[{"text": value, "options": {"fill": {"color": "000000" if r == 0 else "F5F7F8" if r % 2 == 0 else "FFFFFF"},
          "color": "FFFFFF" if r == 0 else "000000", "bold": r == 0 or c == 0, "align": "left"}}
          for c, value in enumerate(row)] for r, row in enumerate(rows)]
entities.append({"id": "scale-gate-table", "display_label": "Four conditions for scaling the research pilot", "kind": "table", "role": "pilot_scale_gate",
                 "bbox_hint": [1224, 288, 649, 473], "geometry_policy": "agent_logical", "z": 5, "meaningful_visible": True,
                 "table_structure": {"rows": cells, "column_widths_px": [358, 291], "row_heights_px": [84, 96, 97, 97, 99]},
                 "style_hint": {"font_family": "Arial", "font_size_px": 24, "cell_margin_px": 20, "color": "#000000",
                                "fill": "#FFFFFF", "stroke": "#B5B5B5", "stroke_width_px": 1, "vertical_alignment": "middle"}})

shape("decision-band", [47, 805, 1826, 122], "#FFF5ED")
shape("decision-accent", [47, 805, 8, 122], "#FD5108")
text("decision-label", "DECISION REQUESTED", [97, 843, 425, 48], 28, "decision-band", bold=True, color="#FD5108", role="call_to_action", middle=True, search=[96, 852, 393, 38])
text("decision-request", "Approve $25k and name a practice sponsor.", [562, 843, 1264, 48], 28, "decision-band", bold=True, role="call_to_action", middle=True, search=[561, 852, 655, 38])

groups = [
    {"id": "capacity-hypothesis", "display_label": "Quantified capacity hypothesis", "semantic_class": "planning calculation",
     "group_reason": "Baseline effort, adoption and time reduction lead to the capacity and monetary equivalent.", "bbox_hint": [47, 229, 645, 553],
     "children": [entity["id"] for entity in entities if entity["id"].startswith(("baseline", "capacity", "metric"))]},
    {"id": "pilot-argument", "display_label": "Why this bounded pilot", "semantic_class": "decision argument",
     "group_reason": "Repeatable tasks, expert control and conditional funding explain the proposed pilot boundary.", "bbox_hint": [700, 229, 528, 550],
     "children": [entity["id"] for entity in entities if entity["id"].startswith("argument")]},
    {"id": "scale-criteria", "display_label": "Observable scale criteria", "semantic_class": "release criteria",
     "group_reason": "The native table preserves all four measurable conditions and their thresholds.", "bbox_hint": [1223, 229, 650, 532],
     "children": ["gate-heading", "scale-gate-table"]},
    {"id": "funding-decision", "display_label": "Bounded funding approval", "semantic_class": "decision request",
     "group_reason": "The shared decision band gives one concrete investment request.", "bbox_hint": [47, 805, 1826, 122],
     "children": ["decision-band", "decision-accent", "decision-label", "decision-request"]},
]
semantic = {"schema_version": "3.2.0", "provenance": {"created_by": "host_agent_visual_reasoning", "source": "accepted_generated_image",
            "source_sha256": hashlib.sha256((WORK/"accepted-slide.png").read_bytes()).hexdigest(), "composition_policy": "accepted_target_geometry_frozen"},
            "entities": entities, "groups": groups,
            "layout_constraints": {"non_overlap_pairs": [["headline", "pilot-scope"], ["scale-gate-table", "decision-band"],
                                                        ["capacity-value-formula", "decision-band"]]}}
(WORK/"semantic-map.json").write_text(json.dumps(semantic, indent=2)+"\n")
handoff = {"selected_assets": [], "sources": ["Host-authored illustrative Northstar Advisory planning model"], "notes": [
    "All quantities are illustrative planning assumptions. Capacity value is not a cash saving.",
    "The 95% gate applies to a sampled test set. Each client release separately requires expert verification and engagement-lead approval.",
    "At least 11 of 15 pilot users must be weekly active. One comparable research task is measured per pilot engagement.",
    "Reconstruction uses a 1920 by 960 substantive canvas, translated down 64 pixels into a 1920 by 1080 presentation with an inherited frame.",
    "Georgia title stays 64 pixels, Arial section and body roles 28 pixels, table 24 pixels and both decision-band texts 28 pixels. Source condensed glyph proportions are not imitated by compressing type.",
    "The shared design specifies an 8-pixel decision bar. Its native width follows that shared value, while the accepted source bar is slightly wider.",
    "No icon, directed connector or raster illustration appears on this opening page. The numeric reasons are ordering labels, and the thin rules separate evidence groups."]}
(WORK/"reconstruction-handoff.json").write_text(json.dumps(handoff, indent=2)+"\n")
