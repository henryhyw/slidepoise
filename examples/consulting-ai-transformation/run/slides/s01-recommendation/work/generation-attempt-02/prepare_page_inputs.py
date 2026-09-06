"""Persist authored body content. The generation compiler binds deck design."""
import json
from pathlib import Path

run=Path(__file__).resolve().parents[1]
outline=json.loads((run/'work/deck-outline.json').read_text())
content={
's01-recommendation':[
 {'role':'subtitle','text':'One practice. 15 consultants. 20 paired research tasks. A 12-week, $25k pilot.'},
 {'role':'metric_reasoning','items':[
  {'value':'10,800 h','label':'Annual research baseline','calculation':'900 engagements × 12 h'},
  {'value':'1,944 h','label':'Potential annual capacity','calculation':'60% adoption × 30% time reduction'},
  {'value':'$243k','label':'Annual capacity equivalent','calculation':'1,944 h × $125 per hour'}]},
 {'role':'argument','heading':'WHY THIS PILOT FIRST','items':[
  {'number':'01','heading':'Focus a repeatable task','detail':'Approved sources, frequent use and comparable inputs.'},
  {'number':'02','heading':'Preserve expert review','detail':'Verify every client claim before release.'},
  {'number':'03','heading':'Fund against evidence','detail':'Practice lead accountable. CFO sponsors the gate.'}]},
 {'role':'native_table','heading':'WEEK-12 SCALE GATE','columns':['Measure','Minimum to scale'],'rows':[
  ['Cycle-time reduction','25%'],['Sampled cited claims verified','95%'],['Critical data exceptions','0'],['Weekly-active pilot users','70% · at least 11 of 15']]},
 {'role':'decision_band','label':'DECISION REQUESTED','message':'Approve $25k and name a practice sponsor.'}],
's02-opportunities':[
 {'role':'subtitle','text':'Capacity creates the opportunity. Control readiness sets the sequence.'},
 {'role':'native_chart','heading':'ANNUAL CAPACITY POTENTIAL','qualification':'Illustrative hours','categories':['Research synthesis','Proposal drafting','Knowledge retrieval'],'values':[1944,1440,1080]},
 {'role':'native_table','columns':['Workflow','Baseline h','Adoption','Time saved'],'rows':[['Research','12','60%','30%'],['Proposal','8','50%','40%'],['Retrieval','5','60%','40%']]},
 {'role':'formula','text':'Annual hours = 900 engagements × baseline h × adoption × time saved'},
 {'role':'native_table','heading':'PILOT SEQUENCING TEST','columns':['Workflow','Control readiness','Owner','Sequence'],'rows':[
  ['Research synthesis','Approved corpus\nExplicit review','Practice lead','START'],
  ['Proposal drafting','Claims and commitments\nneed controls','BD lead','NEXT'],
  ['Knowledge retrieval','Permissions need\ncleanup','Knowledge lead','LATER']]},
 {'role':'argument','heading':'WHY RESEARCH WINS FIRST','items':['Frequent, comparable tasks','A bounded source corpus','A named expert reviewer']},
 {'role':'qualification_in_body','text':'Check task overlap before adding workflow benefits.'},
 {'role':'decision_band','label':'PILOT BOUNDARY','message':'Start with approved-source research synthesis.'}],
's03-operating-model':[
 {'role':'subtitle','text':'A controlled path from permissioned evidence to approved client work.'},
 {'role':'directed_workflow','stages':['Approved sources','Grounded draft','Expert review','Client-ready output']},
 {'role':'native_table','columns':['','Approved sources','Grounded draft','Expert review','Client-ready output'],'rows':[
  ['INPUT','Corpus request','Source pack + task brief','Draft + evidence trail','Signed draft + resolved defects'],
  ['OUTPUT','Versioned source pack','Cited draft + uncertainty flags','Signed review or defect log','Authorized client deliverable'],
  ['OWNER','Source steward','Engagement team','Expert reviewer','Engagement lead'],
  ['RELEASE CONTROL','Verify permissions\nand dates','Check citations\nand evidence gaps','Validate claims\nand quality','Confirm release\napproval']]},
 {'role':'return_relationships','items':[
  {'from':'Expert review','to':'Grounded draft','label':'Reject with defect reasons'},
  {'from':'Grounded draft','to':'Approved sources','label':'Correct sources via exception register'}]},
 {'role':'shared_controls','heading':'SHARED CONTROLS','items':['One register records defects, owners and disposition.','Platform team maintains access controls and audit logs.']},
 {'role':'measurement','heading':'PILOT MEASUREMENT','items':['Compare 20 paired tasks with baseline time logs.','Verify claim samples and record expert review effort.']},
 {'role':'decision_band','label':'RELEASE RULE','message':'No client use without expert and engagement-lead sign-off.'}],
's04-delivery-roadmap':[
 {'role':'subtitle','text':'Owners run the workstreams. Evidence gates release the next phase.'},
 {'role':'native_table','columns':['WORKSTREAM / OWNER','WEEKS 1–2\nApprove & baseline','WEEKS 3–4\nBuild & test','WEEKS 5–8\nPilot & learn','WEEKS 9–12\nProve & decide'],'rows':[
  ['Data & access\nSource steward','Approved corpus\nAccess register','Source refresh\nNamed stewards','Weekly access and\nfreshness checks','Audit closeout\nRelease inventory'],
  ['Workflow & product\nProduct lead','Task mapping\nBaseline time logs','Grounded draft\nVisible citations','15-user pilot\nDefect fixes','Release candidate\nRunbook'],
  ['Quality & controls\nExpert reviewer','Risk boundaries\nReview criteria','Test pack\nRejection reasons','10 reviewed tasks\nError triage','20 completed tasks\nGate evidence'],
  ['Adoption & value\nPractice lead','Sponsor & users\nAgree tracking','Training & support\nMeasurement plan','Weekly usage\nFeedback sessions','Benefit case\nScale recommendation']]},
 {'role':'milestones','items':[
  {'title':'G1 · Week 2','evidence':'Corpus + access signed'},
  {'title':'G2 · Week 4','evidence':'Test pack approved'},
  {'title':'G3 · Week 8','evidence':'10 tasks reviewed'},
  {'title':'G4 · Week 12','evidence':'Practice lead + CFO decide'}]},
 {'role':'dependency_chain','heading':'DEPENDENCIES','items':['Permissions before retrieval tests','Approved test pack before pilot','Quality evidence before benefit case']},
 {'role':'decision_band','label':'STOP RULE','message':'No expansion while critical data exceptions remain open.'}],
's05-investment-decision':[
 {'role':'subtitle','text':'Use the full first-year cost, a realistic ramp and explicit go/no-go tests.'},
 {'role':'formula','heading':'BASE-CASE CAPACITY MODEL','equation':'900 × 12 h × 60% × 30% = 1,944 h','term_labels':['Engagements','Research time','Adoption','Time saved'],'valuation':'1,944 h × $125/h = $243k annual capacity equivalent'},
 {'role':'native_table','heading':'INVESTMENT','columns':['Cost item','Amount'],'rows':[['Implementation','$85k'],['Pilot included','$25k'],['Annual operations','$30k'],['First-year total','$115k']]},
 {'role':'qualification_in_body','text':'Remaining implementation after the pilot $60k.'},
 {'role':'native_table','heading':'FIRST-YEAR SENSITIVITY · 50% RAMP','columns':['Scenario','Adoption','Time saved','Annual h','Annual capacity','First-year value','Net vs $115k'],'rows':[
  ['Downside','40%','20%','864','$108k','$54k','−$61k'],
  ['Base','60%','30%','1,944','$243k','$121.5k','+$6.5k'],
  ['Upside','75%','40%','3,240','$405k','$202.5k','+$87.5k']]},
 {'role':'decision_criteria','items':[
  {'heading':'GO','body':'All four gates hold.\nPractice lead owns rollout.'},
  {'heading':'HOLD','body':'Evidence or usage is weak.\nExtend within an agreed cap.'},
  {'heading':'STOP','body':'A critical data control fails.\nSuspend use and close the issue.'}]},
 {'role':'decision_band','label':'APPROVE $25k NOW','message':'Release the remaining $60k only after the week-12 gate.'}]
}
relationships={
's01-recommendation':[{'type':'calculation','source':'10,800 h baseline','factors':['60% adoption','30% time reduction'],'target':'1,944 h potential annual capacity'},{'type':'conditional_investment','source':'$25k pilot','condition':'Week-12 scale criteria','target':'Remaining $60k'}],
's02-opportunities':[{'type':'comparison','members':['Research synthesis','Proposal drafting','Knowledge retrieval'],'dimensions':['capacity','control readiness','owner','sequence']}],
's03-operating-model':[{'type':'directed_sequence','members':['Approved sources','Grounded draft','Expert review','Client-ready output']},{'type':'feedback','source':'Expert review','target':'Grounded draft','label':'Reject with defect reasons'},{'type':'feedback','source':'Grounded draft','target':'Approved sources','label':'Correct sources via exception register'}],
's04-delivery-roadmap':[{'type':'time_by_workstream','time_windows':['1–2','3–4','5–8','9–12'],'workstreams':['Data & access','Workflow & product','Quality & controls','Adoption & value']},{'type':'dependency','members':['Source permissions','Approved test pack','Pilot quality evidence','Benefit case']}],
's05-investment-decision':[{'type':'scenario_sensitivity','shared_inputs':['900 engagements','12 baseline h','$125 per hour','50% first-year ramp','$115k total first-year cost'],'varied_inputs':['adoption','time reduction']},{'type':'conditional_funding','source':'$25k pilot approval','condition':'Week-12 evidence gate','target':'Remaining $60k implementation'}]
}
for entry in outline['slides']:
 sid=entry['slide_id'];w=run/'slides'/sid/'work'
 intent={'audience_question':entry['communication_job'],'dominant_message':entry['dominant_message'],
  'information_structure':{'type':entry['role'],'description':entry['communication_job']},'required_content':content[sid],
  'semantic_relationships':relationships[sid],'hierarchy':['Shared Georgia claim title','Shared Arial subtitle','Evidence or operating structure','Shared substantive decision band'],
  'evidence':['Host-authored illustrative planning model. The preserved work/planning-assumptions.json carries the exact calculation assumptions.'],
  'assumptions':['Northstar Advisory is fictional. Capacity equivalent is not revenue or cash savings.','The pilot measures one comparable research task per engagement, so 20 tasks correspond to 20 engagements.','The 95% sampled-claim gate does not replace expert verification and approval of each client release.'],
  'open_questions':[],'avoid':['Any generated header, footer, company label, page number, shared-frame rule or repeated source-note strip.','Independent changes to recurring title size, font family or decision-band treatment.','Decorative icons, invented imagery and miniature type.'],
  'visual_obligations':['Generate only the 1920 by 960 substantive canvas at exactly 2:1 aspect ratio. The runtime adds the separate inherited frame.','Use native-friendly text, tables, chart geometry and continuous directed relationships where the content requires them.','Follow the shared deck design. The five pages vary their evidence structures while recurring roles remain consistent.'],
  'user_required_assets':[],'density_intent':'information_rich',
  'explicit_user_visual_requirements':['Georgia claim title at 64 px regular on every page, with no per-page shrinking.','Arial subtitle 32 px regular, body 28 px regular, section labels 28 px bold and table text 24 px.','Every decision band uses pale orange #FFF5ED fill, orange #FD5108 label and left bar, black message, and no surrounding border.','Place all necessary page-specific qualifications in the substantive content. Shared frame wording is excluded from image generation.']}
 (w/'slide-intent.json').write_text(json.dumps(intent,indent=2,ensure_ascii=False)+'\n')
 draft={'style_direction':{'intent':'Dense, readable executive content with Georgia claim titles, Arial supporting roles and one coherent decision-band treatment.','freedom':'Vary the meaningful information layout. Preserve the shared visual roles and body-only canvas.'},'selected_visual_references':[],'selected_assets':[],'selected_components':[]}
 (w/'resource-selection.draft.json').write_text(json.dumps(draft,indent=2,ensure_ascii=False)+'\n')
selection={'selected_visual_references':[],'selected_assets':[],'selected_components':[],'host_selection_reason':'The authored pages use native data, tables and operating relationships. Available table component catalog descriptions use different emphasis treatments. The current shared design supplies the relevant visual roles, so no additional component or icon is selected.','provider_use':'Remote sources are disabled in the resolved run config.'}
(run/'work/deck-resource-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
print('Prepared five body-only intents and draft resource selections')
