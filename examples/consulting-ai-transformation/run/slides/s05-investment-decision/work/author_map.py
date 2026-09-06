"""Serialize host-inspected semantic allocations from the accepted investment image."""
import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent
intent = json.loads((WORK / "slide-intent.json").read_text())
content = intent["required_content"]
entities = []


def text(identifier, value, box, size, group, *, bold=False, color="#000000", family="Arial", role="body", search=None, leading=1.0, middle=False, alignment="left"):
    item = {"id": identifier, "display_label": value.replace("\n", " "), "kind": "text", "role": identifier,
            "text": value, "text_style_role": role, "typography_group": group,
            "bbox_hint": box, "search_bbox_hint": search or box, "geometry_policy": "agent_logical", "z": 20,
            "meaningful_visible": True, "reconstruction_significance": "independent_object",
            "style_hint": {"font_family": family, "font_weight": "bold" if bold else "regular",
                           "target_font_size_px": size, "alignment": alignment, "line_spacing": leading,
                           "vertical_alignment": "middle" if middle else "top",
                           "observed_foreground_color": color, "style_authority": "agent_visual_observation"}}
    if color == "#FD5108":
        item["style_token"] = "call_to_action" if role == "call_to_action" else "data_highlight"
    entities.append(item)


def shape(identifier, box, fill, *, search=None):
    entities.append({"id": identifier, "display_label": identifier.replace("-", " "), "kind": "shape",
                     "shape": "rectangle", "role": "native_presentation_geometry", "bbox_hint": box,
                     "search_bbox_hint": search or box,
                     "geometry_policy": "agent_logical", "z": 1, "meaningful_visible": True,
                     "style_hint": {"fill": fill, "stroke": "none", "stroke_width_px": 0,
                                    "style_authority": "agent_visual_observation"}})


def table(identifier, label, body, box, widths, heights, *, selected_row=None, rightmost_accent=False):
    rows = [body["columns"], *body["rows"]]
    cells = []
    for r, row in enumerate(rows):
        cell_row = []
        for c, value in enumerate(row):
            fill = "000000" if r == 0 else "FFF5ED" if r == selected_row else "F5F7F8" if r % 2 == 0 else "FFFFFF"
            color = "FFFFFF" if r == 0 else "FD5108" if rightmost_accent and c == len(row) - 1 else "000000"
            header_wraps = {"Time saved": "Time\nsaved", "Annual capacity": "Annual\ncapacity",
                            "First-year value": "First-year\nvalue", "Net vs $115k": "Net vs\n$115k"}
            value = header_wraps.get(value, value) if r == 0 else value
            cell_row.append({"text": value, "options": {"fill": {"color": fill}, "color": color,
                             "bold": r == 0 or r == selected_row or (rightmost_accent and c in (0, len(row) - 1)),
                             "align": "left" if c == 0 else "center"}})
        cells.append(cell_row)
    entities.append({"id": identifier, "display_label": label, "kind": "table", "role": identifier,
                     "bbox_hint": box, "geometry_policy": "agent_logical", "z": 5, "meaningful_visible": True,
                     "table_structure": {"rows": cells, "column_widths_px": widths, "row_heights_px": heights},
                     "style_hint": {"font_family": "Arial", "font_size_px": 24,
                                    "cell_margin_px": 6 if rightmost_accent else 14,
                                    "color": "#000000", "fill": "#FFFFFF", "stroke": "#DFE3E6",
                                    "stroke_width_px": 1, "vertical_alignment": "middle"}})


text("headline", intent["dominant_message"], [48, 19, 1824, 80], 64, "claim-title", family="Georgia", role="slide_title", search=[38, 27, 1329, 65])
text("subtitle", content[0]["text"], [48, 103, 1824, 47], 32, "subtitle", role="subtitle", search=[40, 109, 956, 37])
shape("introduction-rule", [48, 165, 1824, 2], "#AAAAAA", search=[39,162,1841,2])
for identifier, value, box, search in [
    ("capacity-heading", content[1]["heading"], [41, 201, 584, 44], [41, 205, 355, 30]),
    ("investment-heading", content[2]["heading"], [633, 201, 377, 44], [633, 205, 170, 29]),
    ("sensitivity-heading", content[4]["heading"], [1061, 201, 819, 44], [1060, 205, 463, 29]),
]:
    text(identifier, value, box, 28, "section-headings", bold=True, role="heading_large", search=search)

for index, (value, x, width, search) in enumerate([
    ("900", 88, 73, [45,271,57,32]), ("×", 174, 30, [122,277,19,20]),
    ("12 h", 218, 78, [154,271,62,32]), ("×", 282, 30, [230,277,19,20]),
    ("60%", 321, 75, [261,271,62,32]), ("×", 391, 30, [332,277,19,20]),
    ("30%", 425, 70, [361,271,61,32]), ("=", 492, 29, [428,279,20,16]),
]):
    text(f"capacity-term-{index}", value, [x, 270, width, 45], 28, "formula-terms", search=search)
text("capacity-result", "1,944 h", [518, 270, 110, 49], 28, "formula-results", bold=True, color="#FD5108", search=[450,266,128,43])

for index, (value, box, search) in enumerate([
    ("Engagements", [37, 324, 158, 45], [34, 325, 111, 25]),
    ("Research\ntime", [193, 324, 111, 68], [153, 322, 72, 51]),
    ("Adoption", [303, 324, 106, 45], [258, 322, 66, 25]),
    ("Time\nsaved", [417, 324, 78, 68], [350, 322, 87, 29]),
]):
    text(f"capacity-term-label-{index}", value, box, 24, "formula-annotations", role="label", search=search, leading=1.1, alignment="center")
shape("capacity-divider", [39, 397, 466, 1], "#B5B5B5")
text("capacity-valuation", "1,944 h × $125/h =", [39, 451, 254, 50], 28, "formula-terms", search=[38, 453, 247, 38])
text("capacity-value", "$243k", [296, 451, 245, 50], 28, "formula-results", bold=True, color="#FD5108", search=[294, 438, 181, 59])
text("capacity-equivalent", "annual capacity equivalent", [41, 502, 578, 43], 28, "body-copy", search=[40, 503, 324, 32])

table("investment-table", "Five-row investment table", content[2], [632, 240, 377, 273], [231, 146], [54, 52, 53, 56, 58], selected_row=4)
text("remaining-investment", content[3]["text"].replace(" after", "\nafter"), [632, 522, 402, 70], 28, "body-copy", search=[631, 531, 400, 31], leading=1.1)
table("scenario-table", "Three scenarios with explicit first-year ramp", content[4], [1061, 240, 819, 300],
      [126, 126, 88, 116, 120, 129, 114], [79, 72, 74, 75], rightmost_accent=True)

shape("criteria-rule", [38, 607, 1842, 2], "#DFE3E6", search=[38,593,1842,2])
shape("criteria-divider-1", [629, 608, 1, 166], "#DFE3E6", search=[629,594,1,180])
shape("criteria-divider-2", [1245, 608, 1, 166], "#DFE3E6", search=[1245,594,1,180])
for index, (item, x) in enumerate(zip(content[5]["items"], [131, 752, 1380])):
    text(f"criterion-heading-{index}", item["heading"], [x, 624, 437, 48], 28, "section-headings", bold=True, role="heading_large", search=[x-2, 631, 127, 41])
    text(f"criterion-body-{index}", item["body"], [x, 676, 491, 91], 28, "criteria-body", search=[x-2, 681, 489, 71], leading=1.35)

shape("decision-band", [48, 793, 1824, 134], "#FFF5ED", search=[38,793,1842,138])
shape("decision-accent", [48, 793, 8, 134], "#FD5108", search=[38,793,18,138])
text("decision-label", content[6]["label"], [100, 832, 420, 52], 28, "decision-band", bold=True, color="#FD5108", role="call_to_action", middle=True, search=[104, 841, 459, 50])
text("decision-message", content[6]["message"], [560, 832, 1265, 52], 28, "decision-band", bold=True, role="call_to_action", middle=True, search=[643, 850, 842, 39])

groups = [
    {"id": "capacity-model", "display_label": "Capacity and valuation assumptions", "semantic_class": "calculation",
     "group_reason": "The baseline volume, time, adoption and reduction produce capacity hours and their monetary equivalent.",
     "bbox_hint": [35, 201, 593, 352], "children": [e["id"] for e in entities if e["id"].startswith("capacity-")]},
    {"id": "cost-model", "display_label": "Full first-year investment", "semantic_class": "investment model",
     "group_reason": "One native table preserves the included pilot, operating costs and total. The separate qualification states the remaining implementation cost.",
     "bbox_hint": [632, 201, 402, 386], "children": ["investment-heading", "investment-table", "remaining-investment"]},
    {"id": "scenario-model", "display_label": "Downside, base and upside", "semantic_class": "scenario comparison",
     "group_reason": "The native table keeps adoption, time saving, hours, ramp and net value together as three comparable scenarios.",
     "bbox_hint": [1061, 201, 819, 339], "children": ["sensitivity-heading", "scenario-table"]},
    {"id": "release-criteria", "display_label": "Go, hold and stop conditions", "semantic_class": "release criteria",
     "group_reason": "Three textual conditions assign the next action without decorative pictograms.", "bbox_hint": [129, 624, 1744, 145],
     "children": [e["id"] for e in entities if e["id"].startswith("criterion-")]},
    {"id": "funding-request", "display_label": "Conditional funding decision", "semantic_class": "decision request",
     "group_reason": "The pilot approval and remaining investment condition are separate native text peers in one recurring decision band.",
     "bbox_hint": [48, 793, 1824, 134], "children": ["decision-band", "decision-accent", "decision-label", "decision-message"]},
]
semantic = {"schema_version": "3.2.0", "provenance": {"created_by": "host_agent_visual_reasoning", "source": "accepted_generated_image",
            "source_sha256": hashlib.sha256((WORK / "accepted-slide.png").read_bytes()).hexdigest(),
            "composition_policy": "accepted_target_geometry_frozen"}, "entities": entities, "groups": groups,
            "layout_constraints": {"non_overlap_pairs": [["headline", "subtitle"], ["investment-table", "scenario-table"],
                ["remaining-investment", "criteria-rule"], ["criterion-body-0", "decision-band"],
                ["criterion-body-1", "decision-band"], ["criterion-body-2", "decision-band"]]}}
(WORK / "semantic-map.json").write_text(json.dumps(semantic, indent=2) + "\n")
handoff = {"selected_assets": [], "sources": intent["evidence"], "notes": [
    "Financial rows and exact funding conditions come from the retained slide intent and illustrative planning model.",
    "The two native tables own 10 and 28 cells. There are no floating duplicate cell text objects, charts, icons or raster objects.",
    "The source image contains a model-added terminal title period. Parent instruction restores the exact upstream title without that period.",
    "The generated body is 1920 by 960 and is translated down 64 pixels into the full 1920 by 1080 native frame.",
    "Shared roles use Georgia 64px, subtitle Arial 32px, section/body/decision Arial 28px and tables Arial 24px.",
    "The parent Agent approved all four formula-term labels as a separate 24px data-annotation level using the configured label role. Research time and Time saved wrap. Factor allocations widen to align each label with its value in normal-width Arial without horizontal compression. Source-ink windows remain tied to the original generated terms.",
    "Actual Office inspection required regular cost-row labels, wider Adoption and First-year value headers, and a two-line 28px remaining-investment qualification. The criterion rule moves down 14px to clear that qualification, with vertical separators shortened to preserve their lower endpoints.",
    "The source exaggerates the orange calculated values, GO/HOLD/STOP headings and decision label. Shared native roles take precedence over those source size variations.",
    "The deck owner reviewed the five actual renders and requested common geometry. The title begins at body x48/y19, subtitle x48/y103 and divider y165. The decision band is [48,793,1824,134], its accent is 8px, its label begins at x100 and its message at x560. Both decision texts use body y832 and height52 with vertical centering. Original source-ink windows stay unchanged.",
    "Capacity equivalent is not a cash saving. The inherited footer carries that shared qualification, and the remaining-$60k qualification stays in the substantive body."]}
(WORK / "reconstruction-handoff.json").write_text(json.dumps(handoff, indent=2) + "\n")
