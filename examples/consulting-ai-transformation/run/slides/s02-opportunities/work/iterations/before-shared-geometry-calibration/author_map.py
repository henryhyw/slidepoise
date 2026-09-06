"""Host-observed source allocations for the accepted opportunity comparison."""
import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent
entities = []


def text(identifier, value, box, size, group, *, bold=False, color="#000000", family="Arial", role="body", search=None, leading=1.0, middle=False, owner=None):
    item = {"id": identifier, "display_label": value.replace("\n", " "), "kind": "text", "role": identifier,
            "text": value, "text_style_role": role, "typography_group": group, "bbox_hint": box,
            "search_bbox_hint": search or box, "geometry_policy": "agent_logical", "z": 20,
            "meaningful_visible": True, "reconstruction_significance": "owned_content" if owner else "independent_object",
            "style_hint": {"font_family": family, "font_weight": "bold" if bold else "regular", "target_font_size_px": size,
                           "alignment": "left", "vertical_alignment": "middle" if middle else "top", "line_spacing": leading,
                           "observed_foreground_color": color, "style_authority": "agent_visual_observation"}}
    if color == "#FD5108":
        item["style_token"] = "data_highlight" if owner else "call_to_action"
    if owner:
        item["render_owner"] = owner
    entities.append(item)


def shape(identifier, box, fill):
    entities.append({"id": identifier, "display_label": identifier.replace("-", " "), "kind": "shape", "shape": "rectangle",
                     "role": "native_presentation_geometry", "bbox_hint": box, "geometry_policy": "agent_logical", "z": 1,
                     "meaningful_visible": True, "style_hint": {"fill": fill, "stroke": "none", "stroke_width_px": 0,
                     "style_authority": "agent_visual_observation"}})


def table(identifier, label, rows, box, columns, heights, *, assumptions=False):
    cells = []
    for r, row in enumerate(rows):
        line = []
        for c, value in enumerate(row):
            options = {"fill": {"color": "000000" if r == 0 else "F5F7F8" if r == 2 else "FFFFFF"},
                       "color": "FFFFFF" if r == 0 else "FD5108" if not assumptions and c == 3 else "000000",
                       "bold": r == 0 or c == 0 or (not assumptions and c == 3),
                       "align": "center" if (assumptions and c > 0) or (not assumptions and c >= 2) else "left"}
            if assumptions and r == 0:
                options["margin"] = 5 if c == 0 else 0
            if not assumptions and c == 2:
                options["margin"] = 0
            line.append({"text": value, "options": options})
        cells.append(line)
    entities.append({"id": identifier, "display_label": label, "kind": "table", "role": "structured_comparison",
                     "bbox_hint": box, "geometry_policy": "agent_logical", "z": 5, "meaningful_visible": True,
                     "table_structure": {"rows": cells, "column_widths_px": columns, "row_heights_px": heights},
                     "style_hint": {"font_family": "Arial", "font_size_px": 24, "cell_margin_px": 10, "color": "#000000",
                                    "fill": "#FFFFFF", "stroke": "#AEB2B8", "stroke_width_px": 1, "vertical_alignment": "middle"}})


text("headline", "Start where value and control readiness meet", [32, 16, 1850, 86], 64, "claim-title", family="Georgia", role="slide_title", search=[30, 29, 1325, 67])
text("subtitle", "Capacity creates the opportunity. Control readiness sets the sequence.", [32, 104, 1849, 48], 32, "subtitle", role="subtitle", search=[31, 115, 1014, 32])
shape("introduction-rule", [33, 165, 1849, 2], "#999DA4")
for identifier, value, box, search in [
    ("capacity-heading", "ANNUAL CAPACITY POTENTIAL", [32, 192, 620, 42], [32, 198, 391, 29]),
    ("sequencing-heading", "PILOT SEQUENCING TEST", [670, 192, 661, 42], [669, 198, 316, 29]),
    ("reason-heading", "WHY RESEARCH WINS FIRST", [1382, 192, 500, 42], [1380, 198, 355, 29]),
]:
    text(identifier, value, box, 28, "section-headings", bold=True, role="heading_large", search=search)
text("chart-unit", "Illustrative hours", [32, 227, 620, 36], 24, "chart-unit", role="label", search=[32, 234, 158, 24])

chart_id = "annual-capacity-chart"
entities.append({"id": chart_id, "display_label": "Annual capacity potential by workflow", "kind": "chart", "role": "quantified_opportunity_comparison",
                 "bbox_hint": [31, 261, 620, 234], "search_bbox_hint": [31, 269, 620, 219], "geometry_policy": "agent_logical", "z": 4,
                 "meaningful_visible": True, "chart_structure": {"type": "bar", "categories": ["Research\nsynthesis", "Proposal\ndrafting", "Knowledge\nretrieval"],
                 "series": [{"name": "Illustrative annual capacity hours", "values": [1944, 1440, 1080]}],
                 "colors": ["#FD5108", "#A1A8B3", "#CBD1D6"], "show_legend": False, "show_values": True,
                 "show_value_gridlines": False, "show_category_axis": True, "show_value_axis": False,
                 "category_order": "reverse", "value_axis_minimum": 0, "value_axis_maximum": 1944, "gap_width_pct": 50,
                 "plot_layout": {"x": 130/620, "y": 0, "w": 353/620, "h": 1}, "data_label_position": "outEnd",
                 "data_label_format_code": '#,##0" h"', "data_font_family": "Arial", "data_font_size_px": 36,
                 "data_label_color": "#FD5108", "data_label_wrap": False}, "style_hint": {"stroke": "none"}})
for identifier, category, box in [("research", "Research\nsynthesis", [31, 280, 129, 53]),
                                 ("proposal", "Proposal\ndrafting", [31, 356, 129, 53]),
                                 ("retrieval", "Knowledge\nretrieval", [31, 429, 129, 55])]:
    text(identifier+"-category", category, box, 24, "source-chart-categories", bold=True, role="label", owner=chart_id)
for identifier, value, box in [("research-value", "1,944 h", [525, 283, 123, 42]),
                              ("proposal-value", "1,440 h", [433, 360, 120, 41]),
                              ("retrieval-value", "1,080 h", [371, 437, 119, 43])]:
    text(identifier, value, box, 36, "source-chart-values", color="#FD5108", role="large_data_number", owner=chart_id)

table("workflow-assumptions", "Explicit assumptions behind the capacity chart",
      [["Workflow", "Baseline h", "Adoption", "Time saved"], ["Research", "12", "60%", "30%"],
       ["Proposal", "8", "50%", "40%"], ["Retrieval", "5", "60%", "40%"]],
      [33, 502, 582, 198], [157, 145, 144, 136], [50, 49, 49, 50], assumptions=True)
text("capacity-formula", "Annual hours = 900 engagements ×\nbaseline h × adoption × time saved", [32, 707, 621, 79], 28, "calculation", leading=1.2,
     search=[31, 718, 490, 59])
table("pilot-sequencing", "Control readiness and accountable workflow sequence",
      [["Workflow", "Control readiness", "Owner", "Sequence"],
       ["Research\nsynthesis", "Approved corpus\nExplicit review", "Practice\nlead", "START"],
       ["Proposal\ndrafting", "Claims and\ncommitments\nneed controls", "BD\nlead", "NEXT"],
       ["Knowledge\nretrieval", "Permissions need\ncleanup", "Knowledge\nlead", "LATER"]],
      [670, 254, 661, 506], [149, 253, 122, 137], [76, 137, 148, 145])

for number, top, number_top, source_title_y, source_number_y, source_detail_y, heading, detail in [
    ("01", 250, 257, 258, 267, 298, "Frequent, comparable tasks", "Many engagements use the\nsame research task."),
    ("02", 400, 398, 409, 408, 447, "A bounded source corpus", "Approved sources limit scope\nand simplify review."),
    ("03", 551, 549, 560, 558, 598, "A named expert reviewer", "An accountable reviewer verifies\noutputs before client release."),
]:
    text("reason-number-"+number, number, [1381, number_top, 72, 66], 48, "reason-numbers", bold=True, role="section_number", search=[1380, source_number_y, 57, 52])
    text("reason-title-"+number, heading, [1471, top, 428, 44], 28, "reason-titles", bold=True, role="heading_large", search=[1470, source_title_y, 403, 35])
    text("reason-detail-"+number, detail, [1471, top+35, 429, 87], 28, "reason-details", leading=1.2, search=[1470, source_detail_y, 413, 68])
shape("reason-divider-1", [1382, 377, 500, 1], "#B5B7BA")
shape("reason-divider-2", [1382, 528, 500, 1], "#B5B7BA")
shape("overlap-note-panel", [1382, 682, 500, 92], "#F5F7F8")
text("overlap-qualification", "Check task overlap before adding\nworkflow benefits.", [1400, 689, 466, 82], 28, "overlap-qualification", leading=1.0,
     search=[1399, 700, 391, 59])
shape("decision-band", [33, 800, 1850, 127], "#FFF5ED")
shape("decision-accent", [33, 800, 8, 127], "#FD5108")
text("decision-label", "PILOT BOUNDARY", [103, 841, 402, 49], 28, "decision-band", bold=True, color="#FD5108", role="call_to_action", middle=True,
     search=[100, 846, 305, 41])
text("decision-message", "Start with approved-source research synthesis.", [510, 841, 1320, 49], 28, "decision-band", bold=True, role="call_to_action", middle=True,
     search=[509, 847, 774, 43])

groups = [
    {"id": "capacity-case", "display_label": "Opportunity calculation", "semantic_class": "quantitative comparison", "bbox_hint": [31, 192, 621, 594],
     "children": ["capacity-heading", "chart-unit", chart_id, "workflow-assumptions", "capacity-formula"],
     "group_reason": "The chart, assumptions and equation expose the same illustrative model."},
    {"id": "readiness-case", "display_label": "Readiness determines sequence", "semantic_class": "decision comparison", "bbox_hint": [670, 192, 661, 568],
     "children": ["sequencing-heading", "pilot-sequencing"], "group_reason": "Workflow, controls, owner and sequence remain in one native table."},
    {"id": "research-case", "display_label": "Research pilot rationale", "semantic_class": "decision argument", "bbox_hint": [1381, 192, 519, 582],
     "children": [item["id"] for item in entities if item["id"].startswith(("reason", "overlap"))],
     "group_reason": "Three reasons explain the recommendation, and the qualification prevents double-counting benefits."},
]
semantic = {"schema_version": "3.2.0", "provenance": {"created_by": "host_agent_visual_reasoning", "source": "accepted_generated_image",
            "source_sha256": hashlib.sha256((WORK/"accepted-slide.png").read_bytes()).hexdigest(), "composition_policy": "accepted_target_geometry_frozen"},
            "entities": entities, "groups": groups,
            "layout_constraints": {"non_overlap_pairs": [["headline", "subtitle"], ["pilot-sequencing", "decision-band"], ["overlap-note-panel", "decision-band"]]}}
(WORK/"semantic-map.json").write_text(json.dumps(semantic, indent=2)+"\n")
handoff = {"selected_assets": [], "sources": ["Host-authored illustrative Northstar Advisory planning model"], "speaker_notes": [
    "This is an illustrative planning model for fictional Northstar Advisory. Annual capacity assumes 900 engagements. Research uses 900 x 12 baseline hours x 60% adoption x 30% time saved = 1,944 hours. The same formula produces 1,440 proposal hours and 1,080 retrieval hours from the displayed assumptions.",
    "The three workflow estimates may overlap and cannot be added without checking task boundaries. Capacity released is not a cash saving. Control readiness determines the proposed sequence, and expert review remains required before any client release."
], "notes": [
    "Values are planning assumptions for a fictional firm. Check task overlap before aggregating workflow benefits.",
    "The chart contains one real workbook-linked series. Category names and numeric labels are native chart components, including the hours suffix. The six source labels are non-emitting chart-owned measurement members.",
    "Native numeric labels explicitly disable wrapping after actual LibreOffice rendering showed its default narrow label allocation split the digits. This preserves one-line values without independent textboxes.",
    "Changing a category in the workbook updates the chart. The separate comparison and assumption tables are independent editable business views and require corresponding authored content updates.",
    "Two native tables retain explicit header/body roles and every row. Owner cells use minimal horizontal padding so full Arial Knowledge remains readable at the shared 24-pixel table size.",
    "The generated first bar is orange and the other bars are gray. Native fills use the exact flat orange and two gray colors from the accepted edit request.",
    "The shared native title, subtitle, section/body, table and decision sizes stay 64, 32, 28, 24 and 28 pixels. Explicit paragraph reflow preserves every word where native Arial is wider than the generated glyphs.",
    "The source has no numeral squares, icons, arrows or raster artwork. The gray overlap warning is substantive content, separate from the inherited frame.",
    "Generation uses the 1920 by 960 substantive body and the runtime adds the separate inherited 64-pixel header and 56-pixel footer."]}
(WORK/"reconstruction-handoff.json").write_text(json.dumps(handoff, indent=2)+"\n")
