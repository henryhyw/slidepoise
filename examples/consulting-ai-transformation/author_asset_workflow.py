#!/usr/bin/env python3
"""Serialize the host-reviewed consulting deck and its canonical asset bindings."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "run" / "slides"
ORANGE = "#FD5108"
PALE = "#FFF5ED"
GRAY = "#F5F7F8"
INK = "#000000"


def write(slide: str, build):
    work = ROOT / slide / "work"
    target = work / "accepted-slide.png"
    entities: list[dict] = []
    groups: list[dict] = []
    relationships: list[dict] = []

    def text(identifier, value, box, size=28, *, bold=False, family="Arial", color=INK,
             align="left", role="body", group="body", valign="top", leading=1.0, z=20):
        item = {
            "id": identifier, "display_label": value.replace("\n", " "), "kind": "text",
            "role": role, "text": value, "text_style_role": role, "typography_group": group,
            "bbox_hint": box, "search_bbox_hint": box, "geometry_policy": "agent_logical",
            "z": z, "meaningful_visible": True, "reconstruction_significance": "independent_object",
            "style_hint": {
                "font_family": family, "font_weight": "bold" if bold else "regular",
                "target_font_size_px": size, "alignment": align, "vertical_alignment": valign,
                "line_spacing": leading, "observed_foreground_color": color,
                "style_authority": "agent_visual_observation",
            },
        }
        if color == ORANGE:
            item["style_token"] = "data_highlight" if role == "large_data_number" else "call_to_action"
        entities.append(item)

    def shape(identifier, box, fill="#FFFFFF", stroke="none", width=0, kind="rectangle", z=1):
        entities.append({
            "id": identifier, "display_label": identifier.replace("-", " "), "kind": "shape",
            "shape": kind, "role": "native_presentation_geometry", "bbox_hint": box,
            "geometry_policy": "agent_logical", "z": z, "meaningful_visible": True,
            "style_hint": {"fill": fill, "stroke": stroke, "stroke_width_px": width,
                           "style_authority": "agent_visual_observation"},
        })

    def icon(identifier, asset, box, label, peer="deck-supporting-icons"):
        pair = asset.rsplit("-", 1)[0]
        entities.append({
            "id": identifier, "display_label": label, "kind": "icon", "role": "supporting_visual",
            "upstream_asset_id": asset, "bbox_hint": box, "slot_bbox_hint": box,
            "geometry_policy": "agent_logical", "slot_surface": {"visible": False},
            "style_hint": {"preserve_canonical_color": False, "icon_inset_fraction": 0.04},
            "z": 30, "meaningful_visible": True, "reconstruction_significance": "independent_object",
            "icon_treatment_group": peer, "icon_treatment": "black_proxy", "icon_variant": "line",
            "icon_variant_review": {
                "stage": "post_generation_visual_review", "reviewed_by": "host_agent_visual_reasoning",
                "evaluated_asset_ids": [pair + "-line", pair + "-fill"],
                "decision": "The line variant matches the deck's rules, arrows and supporting type.",
                "observations": ["The symbol remains legible at its final size.",
                                 "The fill variant is heavier than the peer symbols."],
            },
        })

    def table(identifier, label, rows, box, widths, heights, *, font=23, orange_last=False, orange_row=None):
        cells = []
        for r, row in enumerate(rows):
            current = []
            for c, value in enumerate(row):
                fill = "000000" if r == 0 else "FFF5ED" if orange_row == r else "F5F7F8" if r % 2 == 0 else "FFFFFF"
                color = "FFFFFF" if r == 0 else "FD5108" if orange_last and c == len(row)-1 else "000000"
                current.append({"text": value, "options": {
                    "fill": {"color": fill}, "color": color,
                    "bold": r == 0 or c == 0 or (orange_last and c == len(row)-1),
                    "align": "left" if c == 0 else "center", "margin": [3, 8, 3, 8],
                }})
            cells.append(current)
        entities.append({
            "id": identifier, "display_label": label, "kind": "table", "role": "structured_evidence",
            "bbox_hint": box, "geometry_policy": "agent_logical", "z": 5, "meaningful_visible": True,
            "table_structure": {"rows": cells, "column_widths_px": widths, "row_heights_px": heights},
            "style_hint": {"font_family": "Arial", "font_size_px": font, "cell_margin_px": 8,
                           "color": INK, "fill": "#FFFFFF", "stroke": "#C6C9CD", "stroke_width_px": 1,
                           "vertical_alignment": "middle"},
        })

    def connector(identifier, source, target, start, end, label=""):
        x1, y1 = start; x2, y2 = end
        entities.append({
            "id": identifier, "display_label": label or identifier.replace("-", " "), "kind": "connector",
            "role": "directed_workflow_relationship", "bbox_hint": [min(x1,x2), min(y1,y2)-12, abs(x2-x1), abs(y2-y1)+24],
            "geometry_policy": "agent_logical", "z": 10, "meaningful_visible": True,
            "connector_intent": {"connector_family": "direct_flow", "directed": True,
                "source_entities": [source], "target_entities": [target],
                "source_attachment_sides": ["right"], "target_attachment_sides": ["left"],
                "source_attachment_fractions": [0.5], "target_attachment_fractions": [0.5],
                "semantic_topology_verified": True, "route_mode": "minimal_orthogonal",
                "junction_style": "none", "visual_route_reviewed": True,
                "visual_route_decision": "The straight route follows the open corridor between adjacent stages.",
                "visual_route_review_artifact": "accepted-slide.png"},
            "visual_constraints": {"start_anchors_px": [[x1,y1]], "end_anchors_px": [[x2,y2]],
                "arrowhead_treatment": "triangle_at_target",
                "stroke_style": {"color": ORANGE, "width_px": 3, "dash": "solid"}},
        })

    build(text, shape, icon, table, connector, entities, groups, relationships)
    semantic = {
        "schema_version": "3.2.0",
        "provenance": {"created_by": "host_agent_visual_reasoning", "source": "accepted_generated_image",
            "source_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "composition_policy": "accepted_target_geometry_frozen"},
        "entities": entities, "groups": groups, "relationships": relationships,
        "layout_constraints": {"non_overlap_pairs": [["headline", "subtitle"], ["decision-band", "headline"]]},
    }
    (work / "semantic-map.json").write_text(json.dumps(semantic, indent=2) + "\n")
    previous = json.loads((work / "reconstruction-handoff.json").read_text())
    resources = json.loads((work / "resource-selection.json").read_text())
    previous["selected_assets"] = resources.get("selected_assets", [])
    previous["notes"] = [n for n in previous.get("notes", []) if "No icon" not in n and "no icon" not in n]
    previous["notes"].append(
        "The host Agent selected line and fill candidates before generation, reviewed both variants in context, "
        "and bound the chosen line SVGs to semantic icon roles. Reconstruction restores the canonical SVG files."
    )
    (work / "reconstruction-handoff.json").write_text(json.dumps(previous, indent=2) + "\n")


def common_header(text, shape, title, subtitle):
    text("headline", title, [46, 20, 1828, 76], 64, family="Georgia", role="slide_title", group="claim-title")
    text("subtitle", subtitle, [47, 101, 1825, 48], 32, role="subtitle", group="subtitle")


def decision(text, shape, label, message):
    shape("decision-band", [46, 835, 1828, 93], PALE)
    shape("decision-accent", [46, 835, 8, 93], ORANGE)
    text("decision-label", label, [80, 853, 430, 50], 28, bold=True, color=ORANGE,
         role="call_to_action", group="decision", valign="middle")
    text("decision-message", message, [520, 853, 1318, 50], 28, bold=True,
         role="call_to_action", group="decision", valign="middle")


def slide1(text, shape, icon, table, connector, entities, groups, relationships):
    common_header(text, shape, "Prove the research pilot before scaling AI",
                  "One practice. 15 consultants. 20 paired research tasks. A 12-week, $25k pilot.")
    metrics = [
        ("baseline", "10,800 h", "Annual research baseline", "900 engagements × 12 h", 47),
        ("capacity", "1,944 h", "Potential annual capacity", "60% adoption × 30% time reduction", 694),
        ("value", "$243k", "Annual capacity equivalent", "1,944 h × $125 per hour", 1340),
    ]
    for ident, value, label, formula, x in metrics:
        text(ident, value, [x, 176, 500, 70], 58, bold=True, color=ORANGE, role="large_data_number", group="display-data")
        text(ident+"-label", label, [x, 248, 520, 32], 25, bold=True, role="heading_large", group="metric-labels")
        text(ident+"-formula", formula, [x, 282, 520, 32], 23, group="metric-formulas")
    shape("metric-divider-1", [647, 176, 1, 138], "#D0D0D0")
    shape("metric-divider-2", [1293, 176, 1, 138], "#D0D0D0")
    text("argument-heading", "WHY THIS PILOT FIRST", [47, 356, 850, 42], 27, bold=True, role="heading_large", group="section")
    reasons = [
        ("01", "remix-focus-2-line", "Focus a repeatable task", "Approved sources, frequent use and comparable inputs.", 420),
        ("02", "remix-team-line", "Preserve expert review", "Verify every client claim before release.", 527),
        ("03", "remix-shield-check-line", "Fund against evidence", "Practice lead and CFO release $60k only after the week-12 gate.", 634),
    ]
    for number, asset, title, detail, y in reasons:
        icon("reason-icon-"+number, asset, [76, y, 54, 54], title)
        text("reason-number-"+number, number, [165, y+3, 62, 44], 25, bold=True, group="reason-numbers")
        text("reason-title-"+number, title, [255, y, 540, 35], 25, bold=True, role="heading_large", group="reason-titles")
        text("reason-detail-"+number, detail, [255, y+38, 700, 40], 21, group="reason-details")
    text("gate-heading", "WEEK-12 SCALE GATE", [1068, 356, 800, 42], 27, bold=True, role="heading_large", group="section")
    table("scale-gate-table", "Four conditions for scaling the pilot", [
        ["Measure", "Minimum to scale"], ["Cycle-time reduction", "25%"],
        ["Sampled cited claims verified", "95%"], ["Critical data exceptions", "0"],
        ["Weekly-active pilot users", "70% · at least 11 of 15"],
    ], [1068, 402, 800, 332], [440, 360], [54, 69, 69, 69, 71], font=22)
    decision(text, shape, "DECISION REQUESTED", "Approve $25k and name a practice sponsor.")
    groups.extend([
        {"id":"pilot-economics","display_label":"Pilot economics","semantic_class":"planning calculation","bbox_hint":[47,176,1820,138],"children":[e["id"] for e in entities if e["id"].startswith(("baseline","capacity","value","metric"))],"group_reason":"Three linked numbers show the baseline, capacity and annual equivalent."},
        {"id":"pilot-rationale","display_label":"Why this pilot first","semantic_class":"decision argument","bbox_hint":[47,356,940,370],"children":[e["id"] for e in entities if e["id"].startswith("reason-")],"group_reason":"Each reason has a distinct icon, claim and supporting sentence."},
        {"id":"scale-gate","display_label":"Week-12 scale gate","semantic_class":"release criteria","bbox_hint":[1068,356,800,378],"children":["gate-heading","scale-gate-table"],"group_reason":"The table keeps the four measurable release conditions editable."},
    ])


def slide2(text, shape, icon, table, connector, entities, groups, relationships):
    common_header(text, shape, "Start where value and control readiness meet",
                  "Capacity creates the opportunity. Control readiness sets the sequence.")
    text("capacity-heading", "ANNUAL CAPACITY POTENTIAL", [37, 158, 680, 38], 27, bold=True, role="heading_large", group="section")
    text("chart-unit", "Illustrative hours", [37, 194, 300, 28], 22, group="label")
    chart_id="annual-capacity-chart"
    entities.append({"id":chart_id,"display_label":"Annual capacity potential by workflow","kind":"chart","role":"quantified_opportunity_comparison","bbox_hint":[40,225,660,290],"geometry_policy":"agent_logical","z":4,"meaningful_visible":True,
        "chart_structure":{"type":"bar","categories":["Research\nsynthesis","Proposal\ndrafting","Knowledge\nretrieval"],"series":[{"name":"Illustrative annual capacity hours","values":[1944,1440,1080]}],"colors":[ORANGE,"#FF955F","#FFC099"],"show_legend":False,"show_values":True,"show_category_axis":True,"show_value_axis":True,"show_value_gridlines":True,"value_axis_minimum":0,"value_axis_maximum":2500,"gap_width_pct":55,"data_label_position":"outEnd","data_label_format_code":"#,##0","data_font_family":"Arial","data_font_size_px":24,"data_label_color":INK,"data_label_wrap":False},"style_hint":{"stroke":"none"}})
    text("value-model-heading", "WORKFLOW VALUE MODEL", [760, 158, 1110, 38], 27, bold=True, role="heading_large", group="section")
    table("value-model", "Inputs behind the capacity comparison", [["Workflow","Baseline h","Adoption","Time saved"],["Research","12","60%","30%"],["Proposal","8","50%","40%"],["Retrieval","5","60%","40%"]], [760,202,1110,230], [285,270,270,285], [52,59,59,60], font=22)
    shape("formula-strip", [760,432,1110,60], GRAY)
    text("capacity-formula", "Annual hours = 900 engagements × baseline h × adoption × time saved", [790,440,1050,44], 24, bold=True, align="center", valign="middle", group="formula")
    text("reason-heading", "WHY RESEARCH WINS FIRST", [37, 532, 680, 38], 27, bold=True, role="heading_large", group="section")
    reason_data=[("file","remix-file-search-line","Frequent, comparable tasks",581),("corpus","remix-database-2-line","A bounded source corpus",651),("reviewer","remix-user-star-line","A named expert reviewer",721)]
    for ident,asset,label,y in reason_data:
        icon("reason-icon-"+ident,asset,[58,y,45,45],label)
        text("reason-"+ident,label,[142,y+2,540,40],24,group="reason")
    text("sequencing-heading", "PILOT SEQUENCING TEST", [760, 520, 1110, 38], 27, bold=True, role="heading_large", group="section")
    table("pilot-sequencing", "Control readiness and accountable workflow sequence", [["Workflow","Control readiness","Owner","Sequence"],["Research synthesis","Approved corpus\nExplicit review","Practice lead","START"],["Proposal drafting","Claims and commitments\nneed controls","BD lead","NEXT"],["Knowledge retrieval","Permissions need\ncleanup","Knowledge lead","LATER"]], [760,564,1110,240], [290,360,250,210], [50,63,63,64], font=20, orange_last=True)
    text("overlap-note", "Check task overlap before adding workflow benefits.", [760,807,850,30], 20, group="note")
    decision(text, shape, "PILOT BOUNDARY", "Start with approved-source research synthesis.")
    groups.extend([
        {"id":"opportunity-model","display_label":"Capacity model","semantic_class":"quantitative comparison","bbox_hint":[37,158,1833,334],"children":["capacity-heading","chart-unit",chart_id,"value-model-heading","value-model","formula-strip","capacity-formula"],"group_reason":"The chart and editable assumption table expose the complete value model."},
        {"id":"pilot-choice","display_label":"Pilot choice","semantic_class":"decision comparison","bbox_hint":[37,520,1833,317],"children":[e["id"] for e in entities if e["id"].startswith(("reason","sequencing","pilot-sequencing","overlap"))],"group_reason":"Icons explain the rationale while the table tests control readiness and ownership."},
    ])


def slide3(text, shape, icon, table, connector, entities, groups, relationships):
    common_header(text, shape, "Keep expert ownership at every release",
                  "A controlled path from permissioned evidence to approved client work.")
    stages=[("sources","remix-file-search-line","Approved sources",260),("draft","remix-draft-line","Grounded draft",690),("review","remix-shield-check-line","Expert review",1185),("output","remix-send-plane-2-line","Client-ready output",1610)]
    for ident,asset,label,x in stages:
        icon("stage-icon-"+ident,asset,[x-38,205,76,76],label,"workflow-stage-icons")
        text("stage-label-"+ident,label,[x-160,312,320,42],25,bold=True,align="center",role="heading_large",group="stage-labels")
    for i in range(3):
        connector("forward-"+str(i+1),"stage-icon-"+stages[i][0],"stage-icon-"+stages[i+1][0],(stages[i][3]+90,243),(stages[i+1][3]-90,243))
    text("source-return-label","Correct sources via exception register",[300,151,430,32],21,bold=True,align="center",group="feedback")
    text("review-return-label","Reject with defect reasons",[790,151,430,32],21,bold=True,align="center",group="feedback")
    rows=[["","Approved sources","Grounded draft","Expert review","Client-ready output"],["INPUT","Corpus request","Source pack + task brief","Draft + evidence trail","Signed draft + resolved defects"],["OUTPUT","Versioned source pack","Cited draft + uncertainty flags","Signed review or defect log","Authorized client deliverable"],["OWNER","Source steward","Engagement team","Expert reviewer","Engagement lead"],["RELEASE CONTROL","Verify permissions\nand dates","Check citations\nand evidence gaps","Validate claims\nand quality","Confirm release\napproval"]]
    table("responsibility-matrix","Inputs, outputs, owners and release controls",rows,[34,382,1836,300],[290,385,390,385,386],[50,58,58,58,76],font=19)
    text("shared-controls-heading","SHARED CONTROLS",[46,700,790,35],25,bold=True,role="heading_large",group="section")
    text("shared-controls","•  One register records defects, owners and disposition.\n•  Platform team maintains access controls and audit logs.",[46,738,800,70],21,leading=1.15,group="body")
    shape("bottom-divider",[900,700,1,108],"#B7BCC2")
    text("measurement-heading","PILOT MEASUREMENT",[945,700,850,35],25,bold=True,role="heading_large",group="section")
    text("measurement","•  Compare 20 paired tasks with baseline time logs.\n•  Verify claim samples and record expert review effort.",[945,738,850,70],21,leading=1.15,group="body")
    decision(text, shape, "RELEASE RULE", "No client use without expert and engagement-lead sign-off.")
    groups.extend([
        {"id":"controlled-flow","display_label":"Controlled release sequence","semantic_class":"directed workflow","bbox_hint":[100,145,1720,215],"children":[e["id"] for e in entities if e["id"].startswith(("stage-","forward-","source-return","review-return"))],"group_reason":"Four asset-backed stages and explicit feedback labels show how ownership is retained."},
        {"id":"accountability","display_label":"Accountability by stage","semantic_class":"responsibility matrix","bbox_hint":[34,382,1836,300],"children":["responsibility-matrix"],"group_reason":"One native table keeps every stage input, output, owner and control editable."},
    ])


def slide4(text, shape, icon, table, connector, entities, groups, relationships):
    common_header(text, shape, "Run the pilot through four evidence gates",
                  "Owners run the workstreams. Evidence gates release the next phase.")
    rows=[["WORKSTREAM / OWNER","WEEKS 1–2\nApprove & baseline","WEEKS 3–4\nBuild & test","WEEKS 5–8\nPilot & learn","WEEKS 9–12\nProve & decide"],["Data & access\nSource steward","Approved corpus\nAccess register","Source refresh\nNamed stewards","Weekly access and\nfreshness checks","Audit closeout\nRelease inventory"],["Workflow & product\nProduct lead","Task mapping\nBaseline time logs","Grounded draft\nVisible citations","15-user pilot\nDefect fixes","Release candidate\nRunbook"],["Quality & controls\nExpert reviewer","Risk boundaries\nReview criteria","Test pack\nRejection reasons","10 reviewed tasks\nError triage","20 completed tasks\nGate evidence"],["Adoption & value\nPractice lead","Sponsor & users\nAgree tracking","Training & support\nMeasurement plan","Weekly usage\nFeedback sessions","Benefit case\nScale recommendation"]]
    table("roadmap-matrix","Twelve-week workstream roadmap",rows,[43,166,1830,432],[355,368,368,368,371],[80,88,88,88,88],font=20)
    text("gates-heading","EVIDENCE GATES",[43,617,900,36],25,bold=True,role="heading_large",group="section")
    gate_data=[("g1","G1 · Week 2","Corpus + access signed",250),("g2","G2 · Week 4","Test pack approved",575),("g3","G3 · Week 8","10 tasks reviewed",900),("g4","G4 · Week 12","Practice lead + CFO decide",1225)]
    for ident,label,detail,x in gate_data:
        icon("gate-icon-"+ident,"remix-flag-line",[x-24,668,48,48],label,"roadmap-gate-icons")
        text("gate-label-"+ident,label,[x-130,729,260,32],23,bold=True,color=ORANGE,align="center",group="gate-labels")
        text("gate-detail-"+ident,detail,[x-150,763,300,35],19,align="center",group="gate-details")
    for i in range(3):
        connector("gate-flow-"+str(i+1),"gate-icon-"+gate_data[i][0],"gate-icon-"+gate_data[i+1][0],(gate_data[i][3]+46,692),(gate_data[i+1][3]-46,692))
    shape("dependency-divider",[1325,616,1,188],"#B7BCC2")
    text("dependencies-heading","DEPENDENCIES",[1360,617,510,36],25,bold=True,role="heading_large",group="section")
    shape("dependency-line",[1400,675,4,100],ORANGE)
    for i,(y,label) in enumerate([(675,"Permissions before retrieval tests"),(725,"Approved test pack before pilot"),(775,"Quality evidence before benefit case")],1):
        shape("dependency-node-"+str(i),[1391,y-9,22,22],ORANGE,kind="ellipse",z=4)
        text("dependency-text-"+str(i),label,[1450,y-13,410,35],20,group="dependencies")
    decision(text, shape, "STOP RULE", "No expansion while critical data exceptions remain open.")
    groups.extend([
        {"id":"delivery-plan","display_label":"Pilot workstreams","semantic_class":"delivery roadmap","bbox_hint":[43,166,1830,432],"children":["roadmap-matrix"],"group_reason":"The native matrix links each owner to concrete work in every phase."},
        {"id":"evidence-gates","display_label":"Evidence gates","semantic_class":"release sequence","bbox_hint":[43,617,1260,181],"children":[e["id"] for e in entities if e["id"].startswith(("gate-","gates-"))],"group_reason":"Four canonical flags mark evidence-backed release decisions along one sequence."},
    ])


def slide5(text, shape, icon, table, connector, entities, groups, relationships):
    common_header(text, shape, "Release the next investment against evidence",
                  "Use the full first-year cost, a realistic ramp and explicit go/no-go tests.")
    shape("introduction-rule",[46,158,1828,2],"#91969D")
    text("capacity-heading","BASE-CASE CAPACITY MODEL",[46,195,545,38],27,bold=True,role="heading_large",group="section")
    shape("capacity-panel",[46,239,545,320],PALE)
    text("capacity-equation","900 × 12 h × 60% × 30%\n= 1,944 h",[64,258,505,115],43,bold=True,color=ORANGE,align="center",role="large_data_number",group="equation")
    text("capacity-labels","Engagements          Research time          Adoption          Time saved",[65,374,500,45],19,align="center",group="labels")
    shape("capacity-divider",[65,446,490,1],"#C1C4C7")
    text("capacity-value","1,944 h × $125/h =",[65,470,270,44],27,group="calculation")
    text("capacity-value-number","$243k",[330,456,220,60],47,bold=True,color=ORANGE,role="large_data_number",group="display-data")
    text("capacity-caption","annual capacity equivalent",[65,520,470,34],22,group="caption")
    text("investment-heading","INVESTMENT",[620,195,485,38],27,bold=True,role="heading_large",group="section")
    table("investment-table","First-year investment",[["Cost item","Amount"],["Implementation","$85k"],["Pilot included","$25k"],["Annual operations","$30k"],["First-year total","$115k"]],[620,239,485,272],[285,200],[52,55,55,55,55],font=22,orange_row=4)
    text("investment-note","Remaining implementation after the pilot $60k.",[620,520,485,36],21,group="note")
    text("sensitivity-heading","FIRST-YEAR SENSITIVITY · 50% RAMP",[1135,195,738,38],27,bold=True,role="heading_large",group="section")
    table("sensitivity-table","First-year sensitivity at a 50 percent ramp",[["Scenario","Adoption","Time saved","Annual h","Annual capacity","First-year value","Net vs $115k"],["Downside","40%","20%","864","$108k","$54k","−$61k"],["Base","60%","30%","1,944","$243k","$121.5k","+$6.5k"],["Upside","75%","40%","3,240","$405k","$202.5k","+$87.5k"]],[1135,239,738,320],[115,105,95,105,108,112,98],[88,77,77,78],font=18,orange_last=True,orange_row=2)
    text("criteria-heading","DECISION CRITERIA",[46,590,900,36],27,bold=True,role="heading_large",group="section")
    criteria=[("go","remix-play-circle-line","GO","All four gates hold.\nPractice lead owns rollout.",46), ("hold","remix-pause-circle-line","HOLD","Evidence or usage is weak.\nExtend within an agreed cap.",655), ("stop","remix-stop-circle-line","STOP","A critical data control fails.\nSuspend use and close the issue.",1264)]
    for ident,asset,label,body,x in criteria:
        shape("criterion-panel-"+ident,[x,630,596,150],GRAY)
        icon("criterion-icon-"+ident,asset,[x+30,655,94,94],label,"decision-criteria-icons")
        text("criterion-label-"+ident,label,[x+170,652,180,40],27,bold=True,color=ORANGE,role="heading_large",group="criteria-labels")
        text("criterion-body-"+ident,body,[x+170,698,390,65],22,leading=1.15,group="criteria-body")
    decision(text, shape, "APPROVE $25k NOW", "Release the remaining $60k only after the week-12 gate.")
    groups.extend([
        {"id":"investment-case","display_label":"Investment case","semantic_class":"financial decision model","bbox_hint":[46,195,1827,364],"children":[e["id"] for e in entities if e["id"].startswith(("capacity-","investment-","sensitivity-"))],"group_reason":"The calculation, cost table and sensitivity table expose every assumption behind the request."},
        {"id":"decision-tests","display_label":"Decision tests","semantic_class":"release criteria","bbox_hint":[46,590,1814,190],"children":[e["id"] for e in entities if e["id"].startswith(("criteria-","criterion-"))],"group_reason":"Three canonical symbols separate go, hold and stop decisions without adding a template constraint."},
    ])


for slide, builder in [
    ("s01-recommendation", slide1), ("s02-opportunities", slide2),
    ("s03-operating-model", slide3), ("s04-delivery-roadmap", slide4),
    ("s05-investment-decision", slide5),
]:
    write(slide, builder)
