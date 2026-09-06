"""Host-observed reconstruction of the second s03 candidate on its 1920x960 body."""
import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parent
entities = []


def text(identifier, value, box, size, group, *, bold=False, family="Arial", role="body", color="#000000", align="left", leading=1.0, search=None, valign="top"):
    item = {"id": identifier, "display_label": value.replace("\n", " "), "kind": "text", "role": identifier,
            "text": value, "text_style_role": role, "typography_group": group, "bbox_hint": box,
            "search_bbox_hint": search or box, "geometry_policy": "agent_logical", "z": 20,
            "reconstruction_significance": "independent_object", "meaningful_visible": True,
            "style_hint": {"font_family": family, "font_weight": "bold" if bold else "regular",
                           "target_font_size_px": size, "alignment": align, "line_spacing": leading,
                           "vertical_alignment": valign, "observed_foreground_color": color,
                           "style_authority": "agent_visual_observation"}}
    if color == "#FD5108":
        item["style_token"] = "call_to_action"
    entities.append(item)


def shape(identifier, box, fill="#FFFFFF", stroke="none", width=0, kind="rectangle", z=1):
    entities.append({"id": identifier, "display_label": identifier.replace("-", " "), "kind": "shape", "shape": kind,
                     "role": "native_presentation_geometry", "bbox_hint": box, "geometry_policy": "agent_logical", "z": z,
                     "meaningful_visible": True, "style_hint": {"fill": fill, "stroke": stroke, "stroke_width_px": width,
                                                               "style_authority": "agent_visual_observation"}})


text("headline", "Keep expert ownership at every release", [48, 19, 1824, 80], 64, "claim-title", family="Georgia", role="slide_title", search=[46, 25, 1122, 59])
text("subtitle", "A controlled path from permissioned evidence to approved client work.", [48, 103, 1824, 51], 32, "subtitle", role="subtitle", search=[47, 108, 1160, 34])
shape("introduction-rule", [48, 165, 1824, 2], "#999999")

nodes = [[89, 198, 255, 91], [444, 198, 253, 91], [794, 198, 255, 91], [1144, 198, 284, 91]]
labels = ["Approved\nsources", "Grounded\ndraft", "Expert\nreview", "Client-ready\noutput"]
for index, (box, label) in enumerate(zip(nodes, labels), 1):
    shape(f"stage-{index}", box, "#FFFFFF", "#FD5108", 2)
    text(f"stage-{index}-label", label, [box[0]+10, 207, box[2]-20, 77], 28, "workflow-labels", bold=True, role="heading_large", align="center", leading=0.95,
         search=[box[0]+28, 211, box[2]-56, 66])
for index in range(1, 4):
    source, target = nodes[index-1], nodes[index]
    x1, x2, y = source[0]+source[2], target[0], source[1]+source[3]/2
    entities.append({"id": f"forward-{index}", "display_label": f"{labels[index-1].replace(chr(10), ' ')} to {labels[index].replace(chr(10), ' ')}",
        "kind": "connector", "role": "controlled_workflow_relationship", "bbox_hint": [x1, y-14, x2-x1, 28],
        "geometry_policy": "agent_logical", "z": 10, "meaningful_visible": True,
        "connector_intent": {"connector_family": "direct_flow", "directed": True,
            "source_entities": [f"stage-{index}"], "target_entities": [f"stage-{index+1}"],
            "source_attachment_sides": ["right"], "target_attachment_sides": ["left"],
            "source_attachment_fractions": [0.5], "target_attachment_fractions": [0.5],
            "semantic_topology_verified": True, "route_mode": "minimal_orthogonal", "junction_style": "none",
            "visual_route_reviewed": True, "visual_route_decision": "The observed straight corridor connects adjacent stage owners without crossing text.",
            "visual_route_review_artifact": "accepted-slide.png"},
        "visual_constraints": {"start_anchors_px": [[x1,y]], "end_anchors_px": [[x2,y]], "arrowhead_treatment": "triangle_at_target",
                               "stroke_style": {"color": "#FD5108", "width_px": 3, "dash": "solid"}}})

rows = [
    ["", "Approved sources", "Grounded draft", "Expert review", "Client-ready output"],
    ["INPUT", "Corpus request", "Source pack + task brief", "Draft + evidence trail", "Signed draft + resolved defects"],
    ["OUTPUT", "Versioned source pack", "Cited draft + uncertainty flags", "Signed review or defect log", "Authorized client deliverable"],
    ["OWNER", "Source steward", "Engagement team", "Expert reviewer", "Engagement lead"],
    ["RELEASE CONTROL", "Verify permissions\nand dates", "Check citations\nand evidence gaps", "Validate claims\nand quality", "Confirm release\napproval"],
]
cells = [[{"text": value, "options": {"fill": {"color": "000000" if r == 0 else "F5F7F8" if r%2 == 0 else "FFFFFF"},
          "color": "FFFFFF" if r == 0 else "000000", "bold": r == 0 or c == 0, "align": "left", "margin": [2,8,2,8]}}
          for c,value in enumerate(row)] for r,row in enumerate(rows)]
entities.append({"id": "responsibility-matrix", "display_label": "Inputs, outputs, owners and release controls", "kind": "table", "role": "stage_responsibility_matrix",
                 "bbox_hint": [49,315,1424,333], "geometry_policy": "agent_logical", "z": 5, "meaningful_visible": True,
                 "table_structure": {"rows": cells, "column_widths_px": [277,288,294,275,290], "row_heights_px": [55,65,64,64,85]},
                 "style_hint": {"font_family": "Arial", "font_size_px": 24, "cell_margin_px": 8, "color": "#000000",
                                "fill": "#FFFFFF", "stroke": "#B5B5B5", "stroke_width_px": 1, "vertical_alignment": "middle"}})

for identifier, right, left, label, box in [
    ("source-correction",672,382,"Correct sources via exception register",[326,736,451,42]),
    ("expert-rejection",1072,765,"Reject with defect reasons",[784,736,340,42]),
]:
    commands = [{"op":"M","point":[right,648]}, {"op":"L","point":[right,700]},
                {"op":"C","control1":[right,714],"control2":[right-11,724],"point":[right-25,724]},
                {"op":"L","point":[left+25,724]},
                {"op":"C","control1":[left+11,724],"control2":[left,714],"point":[left,700]},
                {"op":"L","point":[left,648]}]
    entities.append({"id": identifier, "display_label": label, "kind": "shape", "shape": "authored_path", "role": "feedback_relationship",
                     "reconstruction_route": "fitted_freeform", "bbox_hint": [left-12,648,right-left+15,79],
                     "geometry_policy": "agent_logical", "path_commands_px": commands, "z": 11, "meaningful_visible": True,
                     "style_hint": {"fill":"none", "stroke":"#FD5108", "stroke_width_px":3, "end_arrow_type":"triangle", "style_authority":"agent_visual_observation"}})
    text(identifier+"-label", label, box, 24, "feedback-labels", role="label", align="center", search=box)

text("shared-controls-heading", "SHARED CONTROLS", [1515,254,357,46], 28, "section-headings", bold=True, role="heading_large", search=[1514,262,340,30])
text("shared-register", "One register records\ndefects, owners and\ndisposition.", [1540,304,331,92], 28, "supporting-body", leading=0.85, search=[1540,310,331,60])
text("platform-controls", "Platform team maintains\naccess controls and\naudit logs.", [1540,392,331,90], 28, "supporting-body", leading=0.85, search=[1540,382,331,61])
shape("shared-divider", [1515,486,356,1], "#B5B5B5")
text("measurement-heading", "PILOT MEASUREMENT", [1515,514,357,46], 28, "section-headings", bold=True, role="heading_large", search=[1514,521,340,31])
text("baseline-measurement", "Compare 20 paired\ntasks with baseline time\nlogs.", [1540,567,331,92], 28, "supporting-body", leading=0.85, search=[1540,569,331,61])
text("review-measurement", "Verify claim samples\nand record expert review\neffort.", [1540,661,331,92], 28, "supporting-body", leading=0.85, search=[1540,645,331,66])
for index,y in enumerate([316,404,579,673],1):
    shape(f"list-bullet-{index}", [1517,y,8,8], "#000000", kind="ellipse", z=20)

shape("decision-band", [48,793,1824,134], "#FFF5ED")
shape("decision-accent", [48,793,8,134], "#FD5108")
text("decision-label", "RELEASE RULE", [100,832,420,52], 28, "decision-band", bold=True, color="#FD5108", role="call_to_action", search=[112,839,246,38], valign="middle")
text("decision-message", "No client use without expert and engagement-lead sign-off.", [560,832,1265,52], 28, "decision-band", bold=True, role="call_to_action", search=[421,842,1250,37], valign="middle")

groups = [
    {"id":"controlled-flow","display_label":"Controlled release sequence","semantic_class":"directed workflow","group_reason":"Four stages with three clear handovers.","children":[x['id'] for x in entities if x['id'].startswith(('stage-','forward-'))],"bbox_hint":[89,198,1339,91]},
    {"id":"accountability","display_label":"One accountable owner per stage","semantic_class":"responsibility matrix","group_reason":"The native table retains all five columns and five rows.","children":["responsibility-matrix"],"bbox_hint":[49,315,1424,333]},
    {"id":"feedback","display_label":"Two separate correction paths","semantic_class":"feedback relationships","group_reason":"Source correction returns draft to sources. Expert rejection returns review to draft. The observed U corridors do not cross.","children":["source-correction","source-correction-label","expert-rejection","expert-rejection-label"],"bbox_hint":[345,648,769,127]},
    {"id":"operating-controls","display_label":"Shared controls and pilot measurement","semantic_class":"operating assurance","group_reason":"One exception register, platform controls and paired task measurement support the workflow.","children":["shared-controls-heading","shared-register","platform-controls","measurement-heading","baseline-measurement","review-measurement"],"bbox_hint":[1515,254,357,499]},
    {"id":"release-decision","display_label":"Expert and engagement-lead sign-off","semantic_class":"release rule","group_reason":"The shared decision band makes client release conditional on both sign-offs.","children":["decision-band","decision-accent","decision-label","decision-message"],"bbox_hint":[48,793,1824,134]},
]
semantic = {"schema_version":"3.2.0","provenance":{"created_by":"host_agent_visual_reasoning","source":"accepted_generated_image",
    "source_sha256":hashlib.sha256((WORK/'accepted-slide.png').read_bytes()).hexdigest(),"composition_policy":"accepted_target_geometry_frozen"},
    "entities":entities,"groups":groups,"relationships":[
        {"type":"feedback","display_label":"Correct sources via exception register","source":"stage-2","target":"stage-1","representation":"source-correction"},
        {"type":"feedback","display_label":"Reject with defect reasons","source":"stage-3","target":"stage-2","representation":"expert-rejection"}],
    "layout_constraints":{"non_overlap_pairs":[["headline","subtitle"],["responsibility-matrix","decision-band"],["source-correction","expert-rejection"]]}}
(WORK/'semantic-map.json').write_text(json.dumps(semantic,indent=2)+'\n')
handoff = {"selected_assets":[],"sources":["Host-authored illustrative Northstar Advisory planning model"],
    "speaker_notes":[
        "This is an illustrative planning scenario. Twenty paired tasks represent one research task from each of twenty pilot engagements, with ten tasks at the week-eight interim review. The sampled 95% claim-verification gate measures pilot quality. Every client claim still requires expert sign-off and every client release requires engagement-lead approval.",
        "The two curved feedback paths are editable native freeforms. They preserve the observed direction and curve geometry, but moving the table or its columns in Office does not automatically reattach these paths."
    ],"notes":[
    "Twenty measured tasks correspond to twenty pilot engagements, with one comparable research task per engagement. The week-eight interim measurement contains ten tasks.",
    "The sampled 95% claim-verification gate is an experimental quality measure. Every client claim still requires expert sign-off, and every client release requires engagement-lead approval.",
    "The 70% weekly-active user threshold means at least eleven of fifteen users. It is measured across the pilot team.",
    "All substantive content is native editable text, shapes, one 25-cell table, three straight native lines and two open cubic freeforms. No raster objects are needed.",
    "The cubic feedback paths retain the observed round corners. The return heads and tails are aligned with the named responsibility columns at the table bottom. They are editable freeform paths and do not automatically reattach after moving a table column in Office.",
    "Forward connectors retain source and target ownership in the semantic contract and are regenerated from those owners. The emitted Office lines are positioned geometry and do not claim automatic shape attachment.",
    "Source coordinates were observed on this 1920 by 960 accepted body. The shared frame adds sixty-four pixels above and fifty-six below. Shared Georgia64, Arial32/28/24 and decision28 remain unchanged.",
    "Generated narrow glyphs are not reproduced through text compression. Normal native wrapping and local paragraph rhythm preserve Arial28 in the narrow supporting column. Feedback captions use the shared24-pixel label level.",
    "The cross-page host review sets title x48 y19, subtitle x48 y103 and the shared decision band at x48 y793 with height134. The two 28-pixel decision texts share a vertically centered 52-pixel allocation at y832, with label x100 and message x560. Original ink-search windows remain bound to the accepted source."
]}
(WORK/'reconstruction-handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
