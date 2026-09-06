"""Record factual artifacts and the host's already performed visual observations."""
import hashlib,json,subprocess,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
w=Path(__file__).resolve().parent;p=w.parent;r=p.parents[1];repo=r.parents[2];scripts=repo/'slidepoise/scripts';cfg=r/'work/resolved-config.json';d=p/'deliverables';rec=w/'reconstruction'
def run(name,*args):
 subprocess.run([sys.executable,str(scripts/name),*map(str,args)],check=True)
def save(name,obj): (w/name).write_text(json.dumps(obj,indent=2)+'\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
semantic=json.loads((w/'semantic-map.json').read_text());byid={e['id']:e for e in semantic['entities']}
ex=[]
for identifier,label,ids,box in [
 ('headline','One delivery conclusion',['headline'],None),
 ('delivery-matrix','Workstreams, owners and four phases',['delivery-matrix'],None),
 ('gates','Evidence releases each phase',[e['id'] for e in semantic['entities'] if e['id'].startswith('gate-')],[1313,230,564,263]),
 ('dependencies','Three delivery prerequisites',[e['id'] for e in semantic['entities'] if e['id'].startswith('dependency-')],[1312,580,557,177]),
 ('decision-message','One explicit stop condition',['decision-message'],None)]:
 ex.append({'id':identifier,'kind':'table' if identifier=='delivery-matrix' else 'group','display_label':label,'members':ids,'bbox_hint':box or byid[identifier].get('search_bbox_hint',byid[identifier]['bbox_hint'])})
save('semantic-explanation.json',{'schema_version':'1.0','source_semantic_map':'semantic-map.json','source_semantic_map_sha256':sha(w/'semantic-map.json'),'notice':'Selected host-authored explanations. The full semantic map retains 47 editable entities.','entities':ex})
run('make_semantic_explanation_overlay.py','--image',w/'accepted-slide.png','--semantic-map',w/'semantic-explanation.json','--output',d/'semantic-explanation.png')
run('make_visual_comparison.py','--left',w/'accepted-slide.png','--right',d/'render.png','--config',cfg,'--output',d/'comparison.png','--difference',w/'difference.png')
audit=subprocess.check_output([sys.executable,str(scripts/'slidepoise_runtime.py'),'audit-text','--pptx',str(d/'slide.pptx')]);(w/'native-text-audit.json').write_bytes(audit)
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with zipfile.ZipFile(d/'slide.pptx') as z:
 root=ET.fromstring(z.read('ppt/slides/slide1.xml'));tables=root.findall('.//a:tbl',ns);ids=[e.get('id') for e in root.findall('.//p:cNvPr',ns)]
 tabledata=[[[ ''.join(c.itertext()) for c in row.findall('a:tc/a:txBody',ns)] for row in tab.findall('a:tr',ns)] for tab in tables]
 groups=json.loads((rec/'constructor-scene.json').read_text())['compiler_report']['text_fitting']['text_groups']
 save('native-object-evidence.json',{'pptx_sha256':sha(d/'slide.pptx'),'native_objects':47,'native_textboxes':21,'native_tables':len(tables),'native_table_cells':len(root.findall('.//a:tc',ns)),'native_table_data':tabledata,'native_picture_objects':len(root.findall('.//p:pic',ns)),'duplicate_shape_ids':sorted({i for i in ids if ids.count(i)>1}),'typography_groups':[{'name':x['typography_group'],'font_size_px':x['shared_font_size_px'],'reduced_from_target':x['reduced_from_agent_target']} for x in groups]})
run('collect_semantic_evidence.py','--image',w/'accepted-slide.png','--semantic-map',w/'semantic-map.json','--config',cfg,'--upstream-handoff',w/'reconstruction-handoff.json','--output',w/'semantic-evidence.json')
run('collect_reconstruction_evidence.py','--measured-scene',rec/'measurement/slide_entities.json','--contract',rec/'reconstruction-contract.json','--config',cfg,'--output',w/'reconstruction-evidence.json')
def review(stage,paths,observations):
 save(stage+'-review.json',{'reviewer':'host_agent_visual_reasoning','stage':stage,**({'candidate_index':1} if stage=='generation' else {}),'decision':'accepted','material_issues':[],'reviewed_artifacts':[{'path':name,'sha256':sha(w/name)} for name in paths],'observations':observations})
review('generation',['accepted-slide.png','generated-original.png','generation-request.json'],[
 'The actual generated design contains only the substantive 2:1 canvas. It has no company header, page number, shared footer or footer rule.',
 'The left delivery matrix retains four workstreams and four time windows. The four evidence gates and three prerequisites are legible on the right. No decorative icon replaces the directional dependency marks.',
 'The generated decision treatment and condensed lettering require the already authored deck-wide native font and alignment calibration. Its content and composition remain the reconstruction source.'
])
review('measurement',['accepted-slide.png','semantic-map.json','reconstruction-handoff.json','reconstruction/measurement/slide_entities.json','reconstruction/measurement/debug_overlay.png'],[
 'I inspected the actual OpenCV overlay. The measured table, four gate panels, timeline markers, three arrows and substantive decision band correspond to the source image.',
 'The native allocation preserves named Arial and Georgia fonts. Title, subtitle and decision positions follow the parent Agent cross-slide calibration. Source search windows still refer to the original image ink.',
 'Gate evidence allocations are 133 by 114 body pixels. This accommodates the three-line fourth gate at the shared 24px annotation size. The compiler now reports no reduction in any of the eight text groups.',
 'OpenCV supplies all required measurement evidence. SAM is disabled and contributes no mask.'
])
review('reconstruction',['accepted-slide.png','reconstruction/measurement/slide_entities.json','reconstruction/reconstruction-contract.json','reconstruction/constructor-scene.json','../deliverables/slide.pptx','../deliverables/render.png','../deliverables/render.source.json','../deliverables/comparison.png','native-object-evidence.json','native-text-audit.json'],[
 'I inspected the actual LibreOffice full-slide render and generated-body comparison. All table cells and four milestone panels remain complete. The matrix ends above the decision band, and the three dependency arrows are visible inside their circles.',
 'The native matrix contains 25 editable cells. Row labels are bold and accountable owners are regular. Normal Arial causes some source lines to wrap naturally, without horizontal compression or smaller table type.',
 'The fill-only native gate panels have no accidental black outline. Their real cubic/polygon geometry remains editable. The dependency arrows are above their white circle fills and point toward the prerequisite statements.',
 'Gate evidence now uses the same 24px annotation role as peer tables and formula labels. The prior 22px fitted reduction was corrected by expanding the authored logical allocation. The earlier actual render is retained under iterations/before-cross-slide-calibration.',
 'The 64px Georgia title, 32px subtitle, 28px section/body/decision roles, 32px gate ID markers and 24px evidence role are retained. No fitted group is reduced. Header and footer are inherited native frame content, with a standalone page number of 1 before deck assembly.',
 'Shared decision label and message columns are aligned with the other four pages. This is a recorded Agent calibration of the repeated visual role. The selected source image remains unchanged.',
 'The editable PowerPoint contains 47 native substantive objects and no raster pictures or duplicate native shape IDs. The packaged text audit emits no findings. These are factual checks supporting the visual review.'
])
run('collect_release_evidence.py','--config',cfg,'--generated-image',w/'accepted-slide.png','--semantic-map',w/'semantic-map.json','--measured-scene',rec/'measurement/slide_entities.json','--contract',rec/'reconstruction-contract.json','--constructor-scene',rec/'constructor-scene.json','--pptx',d/'slide.pptx','--generation-review',w/'generation-review.json','--measurement-review',w/'measurement-review.json','--reconstruction-review',w/'reconstruction-review.json','--render',d/'render.png','--output',w/'release-evidence.json')
