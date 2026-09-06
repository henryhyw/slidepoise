"""Host-observed semantic allocations for the current substantive roadmap."""
import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent
entities = []


def text(identifier, value, box, size, group, *, bold=False, color="#000000", family="Arial", role="body", search=None, align="left", leading=1.0, middle=False):
    item = {"id": identifier, "display_label": value.replace("\n", " "), "kind": "text", "text": value,
            "role": identifier, "text_style_role": role, "typography_group": group,
            "bbox_hint": box, "search_bbox_hint": search or box, "geometry_policy": "agent_logical", "z": 30,
            "meaningful_visible": True, "style_hint": {"font_family": family, "font_weight": "bold" if bold else "regular",
                "target_font_size_px": size, "alignment": align, "line_spacing": leading,
                "vertical_alignment": "middle" if middle else "top", "observed_foreground_color": color,
                "color": color, "style_authority": "agent_visual_observation"}}
    if color == "#FD5108":
        item["style_token"] = "call_to_action"
    entities.append(item)


def shape(identifier, box, fill, *, preset="rectangle", stroke="none", width=0, z=5):
    entities.append({"id": identifier, "display_label": identifier.replace("-", " "), "kind": "shape", "shape": preset,
        "bbox_hint": box, "geometry_policy": "agent_logical", "z": z, "meaningful_visible": True,
        "style_hint": {"fill": fill, "stroke": stroke, "stroke_width_px": width, "style_authority": "agent_visual_observation"}})


def path(identifier, box, commands, color="#FD5108", width=2, fill="none", z=10):
    entities.append({"id": identifier, "display_label": identifier.replace("-", " "), "kind": "shape", "shape": "authored_path",
        "bbox_hint": box, "geometry_policy": "agent_logical", "z": z, "meaningful_visible": True,
        "reconstruction_route": "fitted_freeform", "path_commands_px": commands,
        "style_hint": {"fill": fill, "stroke": color, "stroke_width_px": width, "style_authority": "agent_visual_observation"}})


text("headline", "Run the pilot through four evidence gates", [48, 19, 1825, 80], 64, "claim-title", family="Georgia", role="slide_title", search=[47, 27, 1205, 71])
text("subtitle", "Owners run the workstreams. Evidence gates release the next phase.", [48, 103, 1824, 50], 32, "subtitle", role="subtitle", search=[48, 109, 958, 40])
shape("introduction-rule", [48, 165, 1824, 2], "#AAAAAA")

content = [
    ["WORKSTREAM / OWNER", "WEEKS 1–2\nApprove & baseline", "WEEKS 3–4\nBuild & test", "WEEKS 5–8\nPilot & learn", "WEEKS 9–12\nProve & decide"],
    ["Data & access\nSource steward", "Approved corpus\nAccess register", "Source refresh\nNamed stewards", "Weekly access and\nfreshness checks", "Audit closeout\nRelease inventory"],
    ["Workflow & product\nProduct lead", "Task mapping\nBaseline time logs", "Grounded draft\nVisible citations", "15-user pilot\nDefect fixes", "Release candidate\nRunbook"],
    ["Quality & controls\nExpert reviewer", "Risk boundaries\nReview criteria", "Test pack\nRejection reasons", "10 reviewed tasks\nError triage", "20 completed tasks\nGate evidence"],
    ["Adoption & value\nPractice lead", "Sponsor & users\nAgree tracking", "Training & support\nMeasurement plan", "Weekly usage\nFeedback sessions", "Benefit case\nScale recommendation"],
]
rows = []
for r, row in enumerate(content):
    cells = []
    for c, value in enumerate(row):
        if r and c == 0:
            label, owner = value.split("\n")
            value = [{"text": label, "options": {"bold": True}}, {"text": "\n" + owner, "options": {"bold": False}}]
        cells.append({"text": value, "options": {"bold": r == 0, "color": "FFFFFF" if r == 0 else "000000",
            "fill": {"color": "000000" if r == 0 else "F5F7F8" if r % 2 == 0 else "FFFFFF"},
            "align": "center" if r == 0 else "left", "valign": "middle", "margin": [3, 5, 3, 5],
            "paraSpaceAfter": 0, "lineSpacingMultiple": 1.0}})
    rows.append(cells)
entities.append({"id": "delivery-matrix", "display_label": "Workstreams, accountable owners and four delivery phases", "kind": "table",
    "role": "time_and_accountability_matrix", "bbox_hint": [50, 187, 1223, 565], "geometry_policy": "agent_logical", "z": 15,
    "meaningful_visible": True, "table_structure": {"rows": rows, "column_widths_px": [274, 249, 233, 226, 241],
        "row_heights_px": [95, 120, 116, 115, 119]},
    "style_hint": {"font_family": "Arial", "font_size_px": 24, "cell_margin_px": 16, "color": "#000000",
        "fill": "#FFFFFF", "stroke": "#B5B5B5", "stroke_width_px": 1, "vertical_alignment": "middle"}})

text("gates-heading", "EVIDENCE GATES", [1335, 178, 530, 43], 28, "section-headings", bold=True, role="heading_large", search=[1334, 185, 206, 27])
shape("gate-timeline", [1377, 245, 435, 2], "#FD5108", z=10)
for n, x, marker_x, week, evidence in [
    (1, 1313, 1378, "Week 2", "Corpus +\naccess\nsigned"),
    (2, 1454, 1522, "Week 4", "Test pack\napproved"),
    (3, 1596, 1665, "Week 8", "10 tasks\nreviewed"),
    (4, 1740, 1812, "Week 12", "Practice\nlead + CFO\ndecide"),
]:
    path(f"gate-{n}-field", [x, 254, 137, 238], [
        {"op": "M", "point": [x, 254]}, {"op": "L", "point": [x+112, 254]},
        {"op": "L", "point": [x+137, 264]}, {"op": "L", "point": [x+137, 492]},
        {"op": "L", "point": [x, 492]}, {"op": "Z"}], color="none", width=0, fill="#FFF5ED", z=5)
    shape(f"gate-{n}-marker", [marker_x-15, 231, 30, 30], "#FFFFFF", preset="ellipse", stroke="#FD5108", width=7, z=15)
    text(f"gate-{n}-label", f"G{n}", [x+10, 279, 117, 42], 32, "gate-labels", bold=True, color="#FD5108", role="call_to_action", align="center", search=[x+34, 285, 70, 36])
    text(f"gate-{n}-week", week, [x+5, 318, 127, 38], 28, "gate-weeks", bold=True, role="heading_large", align="center", search=[x+20, 322, 108, 31])
    shape(f"gate-{n}-rule", [x+24, 363, 88, 1], "#FD5108", z=10)
    text(f"gate-{n}-evidence", evidence, [x+2, 375, 133, 114], 24, "gate-evidence", role="label", align="center", leading=1.0, search=[x+3, 387, 133, 98])

shape("gates-bottom-rule", [1300, 510, 586, 1], "#B5B5B5")
text("dependencies-heading", "DEPENDENCIES", [1330, 526, 535, 43], 28, "section-headings", bold=True, role="heading_large", search=[1330, 533, 188, 30])
for n, y, message in [(1, 580, "Permissions before retrieval tests"),
                       (2, 647, "Approved test pack before pilot"),
                       (3, 714, "Quality evidence before benefit case")]:
    shape(f"dependency-{n}-circle", [1328, y, 42, 42], "#FFFFFF", preset="ellipse", stroke="#FD5108", width=1.5, z=12)
    path(f"dependency-{n}-arrow", [1338, y+11, 22, 22], [
        {"op": "M", "point": [1338, y+21]}, {"op": "L", "point": [1360, y+21]},
        {"op": "M", "point": [1350, y+11]}, {"op": "L", "point": [1360, y+21]}, {"op": "L", "point": [1350, y+31]}], width=2, z=20)
    text(f"dependency-{n}-text", message, [1389, y+1, 480, 44], 28, "dependency-statements", search=[1387, y+10, 470, 30])
    if n < 3:
        shape(f"dependency-{n}-rule", [1312, y+52, 555, 1], "#B5B5B5")

shape("decision-band", [48, 793, 1824, 134], "#FFF5ED")
shape("decision-accent", [48, 793, 8, 134], "#FD5108", z=10)
text("decision-label", "STOP RULE", [100, 832, 420, 52], 28, "decision-band", bold=True, color="#FD5108", role="call_to_action", middle=True, search=[98, 837, 217, 49])
text("decision-message", "No expansion while critical data exceptions remain open.", [560, 832, 1265, 52], 28, "decision-band", bold=True, role="call_to_action", middle=True, search=[406, 843, 834, 42])

groups = [
    {"id": "workstream-plan", "display_label": "Four accountable workstreams across the pilot", "semantic_class": "time_matrix", "children": ["delivery-matrix"],
     "group_reason": "The matrix retains each time window and accountable owner as a native table."},
    {"id": "evidence-gates", "display_label": "Evidence releases the next phase", "semantic_class": "ordered_milestones",
     "children": [e["id"] for e in entities if e["id"].startswith("gate")], "group_reason": "Four dated milestones share an evidence hierarchy, with an explicit final funding owner."},
    {"id": "dependencies", "display_label": "Prerequisites for delivery", "semantic_class": "release_dependencies",
     "children": [e["id"] for e in entities if e["id"].startswith("dependenc")], "group_reason": "Each directional marker points to an authored prerequisite statement."},
    {"id": "stop-condition", "display_label": "Critical control failures stop expansion", "semantic_class": "decision_condition",
     "children": ["decision-band", "decision-accent", "decision-label", "decision-message"], "group_reason": "One shared decision treatment highlights the restriction."},
]
by_id = {entity["id"]: entity for entity in entities}
for group in groups:
    boxes = [by_id[identifier]["bbox_hint"] for identifier in group["children"]]
    x, y = min(b[0] for b in boxes), min(b[1] for b in boxes)
    group["bbox_hint"] = [x, y, max(b[0]+b[2] for b in boxes)-x, max(b[1]+b[3] for b in boxes)-y]

semantic = {"schema_version": "3.2.0", "provenance": {"created_by": "host_agent_visual_reasoning", "source": "accepted_generated_image",
    "source_sha256": hashlib.sha256((WORK/"accepted-slide.png").read_bytes()).hexdigest(), "composition_policy": "accepted_target_geometry_frozen"},
    "entities": entities, "groups": groups, "layout_constraints": {"non_overlap_pairs": [["headline", "subtitle"], ["delivery-matrix", "decision-band"]]}}
(WORK/"semantic-map.json").write_text(json.dumps(semantic, indent=2, ensure_ascii=False)+"\n")
handoff = {"selected_assets": [], "sources": ["Host-authored illustrative planning model"], "speaker_notes": ["Each pilot engagement supplies one research task. Twenty paired tasks correspond to twenty engagements.", "The practice lead and CFO release scale funding only after the evidence gates are reviewed. Critical data exceptions stop expansion."], "notes": [
    "Each pilot engagement supplies one research task. Twenty tasks correspond to twenty engagements.",
    "The matrix, milestone panels, small dependency arrows and decision band are native presentation geometry. No canonical asset is implied.",
    "Georgia title 64px, Arial subtitle 32px, section/body 28px, table and gate evidence 24px. Gate dates use the body heading level and gate IDs use a separate 32px marker level.",
    "Native font proportions preserve the named font families. Source condensed glyph shapes are not imitated through horizontal compression.",
    "Header and footer are inherited from the resolved shared frame. All mapped source geometry belongs to the 1920 by 960 body canvas.",
    "The shared decision text and 8px accent follow the deck's explicit visual roles, replacing the image model's oversized accent and label treatment."]}
(WORK/"reconstruction-handoff.json").write_text(json.dumps(handoff, indent=2)+"\n")
