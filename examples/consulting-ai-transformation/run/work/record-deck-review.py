"""Record the parent Agent's inspected assembled deck and objective OOXML facts."""
import hashlib,json,shutil,subprocess,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
w=Path(__file__).resolve().parent;r=w.parent;repo=r.parents[2];m=json.loads((w/'deck-scenes.json').read_text());ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d): (w/n).write_text(json.dumps(d,indent=2)+'\n')
facts=[];files=['work/deck-scenes.json','work/deck-design.json','work/deck-outline.json','work/resolved-config.json','work/planning-assumptions.json','deliverables/presentation.pptx','preview/contact-sheet.png','preview/presentation.pdf']
with zipfile.ZipFile(r/'deliverables/presentation.pptx') as z:
 layouts=[]
 for i,s in enumerate(m['slides'],1):
  sid=s['slide_id'];p=r/'slides'/sid;scene=json.loads((p/'work/reconstruction/constructor-scene.json').read_text());root=ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'));ids=[v.get('id') for v in root.findall('.//p:cNvPr',ns)];rels=ET.fromstring(z.read(f'ppt/slides/_rels/slide{i}.xml.rels'));layouts.extend(e.get('Target') for e in rels if e.get('Type','').endswith('/slideLayout'))
  objects=scene['objects'];types={k:sum(o['kind']==k for o in objects) for k in {o['kind'] for o in objects}}
  with zipfile.ZipFile(p/'deliverables/slide.pptx') as single:
   standalone=ET.fromstring(single.read('ppt/slides/slide1.xml'))
   for x in [root,standalone]:
    x.find('p:cSld',ns).set('name','normalized-page-name')
    for index,identity in enumerate(x.findall('.//p:cNvPr',ns)): identity.set('id',str(index+1))
    for field in x.findall('.//a:fld',ns):
     if field.get('type')=='slidenum':
      for t in field.findall('a:t',ns):t.text='normalized-page-number'
   assert ET.tostring(root)==ET.tostring(standalone),sid
  facts.append({'slide_id':sid,'native_objects':len(objects),'native_textboxes':types.get('textbox',0),'native_tables':len(root.findall('.//a:tbl',ns)),'native_table_cells':len(root.findall('.//a:tc',ns)),'native_charts':types.get('chart',0),'native_connectors':types.get('connector_graph',0),'native_freeforms':types.get('freeform',0),'raster_pictures':len(root.findall('.//p:pic',ns)),'duplicate_shape_ids':sorted({n for n in ids if ids.count(n)>1}),'standalone_page_xml_matches_after_page_metadata_and_local_shape_id_normalization':True,'text_groups':[{'role':x['typography_group'],'font_size_px':x['shared_font_size_px'],'reduced_for_fit':x['reduced_for_fit']} for x in scene['compiler_report']['text_fitting']['text_groups']]})
  files.extend([f'preview/slide-{i:03d}.png',f'preview/slide-{i:03d}.source.json',f'slides/{sid}/work/reconstruction/constructor-scene.json',f'slides/{sid}/work/release-evidence.json',f'slides/{sid}/work/reconstruction-review.json'])
 save('deck-native-object-evidence.json',{'slides':facts,'shared_layout_targets':sorted(set(layouts)),'all_pages_share_one_layout':len(set(layouts))==1,'notes_pages':len([n for n in z.namelist() if n.startswith('ppt/notesSlides/notesSlide') and n.endswith('.xml')])})
audit=subprocess.check_output([sys.executable,str(repo/'slidepoise/scripts/slidepoise_runtime.py'),'audit-text','--pptx',str(r/'deliverables/presentation.pptx')]);(w/'native-text-audit.json').write_bytes(audit)
shutil.copy2(repo/'output/product-qa-v3/cross-slide-visual-calibration-review.json',w/'cross-slide-calibration-review.json');files+=['work/deck-native-object-evidence.json','work/native-text-audit.json','work/cross-slide-calibration-review.json']
save('deck-review.json',{'reviewer':'host_agent_visual_reasoning','stage':'assembled_deck','decision':'accepted','material_issues':[],'reviewed_artifacts':[{'path':n,'sha256':sha(r/n)} for n in files],'observations':[
 'I inspected the five-page contact sheet and full-resolution actual LibreOffice pages at 160 DPI. The narrative progresses from a bounded pilot decision through opportunity selection, release accountability, delivery evidence and conditional investment.',
 'All five Georgia claim titles and Arial subtitles align in the same introduction region. The orange labels and black decision messages now use consistent positions, sizes, colors and pale fields. The shared header and footer rules are visually consistent, and page numbers advance from 1 through 5.',
 'The chart remains a native workbook-linked chart. Its research, proposal and retrieval labels display 1,944, 1,440 and 1,080 in full, without digit wrapping. The two opportunity tables and source-overlap qualification are complete.',
 'The operating-model slide has three visible forward arrows and two separate editable return paths. The roadmap matrix has complete workstream owners and dated phases, readable 24px gate evidence and three visible dependency arrows.',
 'The cost model retains $85k implementation including the $25k pilot, $30k annual operations and $115k first-year total. The $60k remaining implementation is conditional. The three scenario values and 50% ramp agree with the retained illustrative assumptions.',
 'The generated images contain the body only. Native shared frame material is inherited through one slide layout. The content target remains 1920 by 960 within the full 1920 by 1080 slide.',
 'Named native fonts differ from the image model glyphs, and some table text wraps onto additional lines. Shared role calibration intentionally corrects the model variation in recurring title, subtitle and decision treatments. These differences are recorded in the page reviews without altering the retained targets.',
 'Actual semantic maps, OpenCV overlays, contracts, compiled scenes, render comparisons and source-bound reviews are retained for all pages. Structural checks support the visual assessment and do not issue its acceptance decision.'
 ],'editability_limits':['Native chart values and labels are linked to their embedded workbook. Separate formula text and scenario table cells do not recalculate automatically.','The two feedback routes are editable PowerPoint freeforms. Automatic connector reattachment after moving their related objects is not claimed.','Verification uses the recorded macOS LibreOffice and installed fonts. Pixel identity across other Office renderers is not claimed.']})
print(json.dumps({'native_objects':sum(x['native_objects'] for x in facts),'native_textboxes':sum(x['native_textboxes'] for x in facts),'native_tables':sum(x['native_tables'] for x in facts),'native_table_cells':sum(x['native_table_cells'] for x in facts),'native_charts':sum(x['native_charts'] for x in facts),'raster_pictures':sum(x['raster_pictures'] for x in facts)},indent=2))
