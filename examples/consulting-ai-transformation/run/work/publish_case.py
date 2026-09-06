"""Stage inspected native output and retained evidence before the atomic replacement."""
import hashlib,json,shutil,subprocess,sys,zipfile
from pathlib import Path
r=Path(__file__).resolve().parents[1];repo=r.parents[2];case=r.parent/'consulting-v3-case';live=repo/'examples/consulting-ai-transformation'
assert case.is_dir() and (case/'run').is_dir()
# Refresh the staged run with finalized reviews, the actual edit proof and rebuild records.
shutil.copytree(r,case/'run',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
(case/'assets').mkdir(exist_ok=True);(case/'deliverables').mkdir(exist_ok=True)
shutil.copytree(r/'preview',case/'preview',dirs_exist_ok=True)
shutil.copy2(r/'deliverables/presentation.pptx',case/'deliverables/presentation.pptx');shutil.copy2(r/'preview/presentation.pdf',case/'deliverables/presentation.pdf');shutil.copy2(r/'preview/contact-sheet.png',case/'assets/contact-sheet.png')
m=json.loads((live/'showcase.json').read_text());o=json.loads((r/'work/deck-outline.json').read_text());m['revision']=3;m['canvas']={'full_slide_px':[1920,1080],'content_region_px':[0,64,1920,960]};m['downloads']={'pptx':'deliverables/presentation.pptx'}
for i,(s,outline) in enumerate(zip(m['slides'],o['slides']),1):
 sid=outline['slide_id'];assert sid==s['id'];s['title']=outline['dominant_message'];p=r/'slides'/sid
 for source,suffix in [(p/'work/accepted-slide.png','target'),(r/f'preview/slide-{i:03d}.png','render'),(p/'deliverables/semantic-explanation.png','semantic')]:shutil.copy2(source,case/'assets'/f'{sid}-{suffix}.png')
 for candidate in [p/'work/semantic-explanation.json',p/'work/semantic-explanation-map.json']:
  if candidate.exists():shutil.copy2(candidate,case/'assets'/f'{sid}-semantic.json');break
m['process'][2].update(title='Explore the content area',description='One compiled brief carries the argument and shared design into a 2:1 body image. The PowerPoint adds the common frame.')
m['process'][7].update(title='Calibrate across the deck',description='The Agent compares all five rendered pages and aligns recurring titles, type sizes and decision bands. The review keeps the observed differences and their corrections.',artifact='run/work/cross-slide-calibration-review.json')
(case/'showcase.json').write_text(json.dumps(m,indent=2)+'\n')
(case/'README.md').write_text('''# A controlled path to shared AI capability

A five-page sample strategy presentation for the fictional Northstar Advisory. It connects a research-synthesis pilot to opportunity selection, release accountability, a 12-week roadmap and conditional investment.

All figures are illustrative planning assumptions. Capacity value is not cash savings. The sampled 95% quality threshold remains separate from expert verification and approval of each client release.

## The presentation

The delivered PowerPoint contains 181 native substantive objects, including 111 textboxes, seven tables with 130 cells, one workbook-linked chart, three forward connectors and nine editable freeforms. Two freeforms are the operating model's feedback paths. There are no raster pictures in this Consulting deck.

The full slide is 1920 by 1080. Image generation produces only the 1920 by 960 content region, beginning 64 pixels below the top of the full slide. A shared native layout supplies the company header and footer. The page number is a native slide field. The Agent reviewed all five actual renders together and calibrated recurring title, subtitle and decision treatments.

The chart values and numeric labels are linked to its workbook. Separate formula text and scenario table cells are editable and do not recalculate automatically. Named native fonts differ from generated lettering. Some table entries use additional lines to preserve their common font size. Automatic reattachment of the feedback paths after moving other objects is not claimed.

## Evidence and reproduction

`run/` retains the actual generated candidates, compiled creative requests, selected body targets, semantic maps, OpenCV overlays, contracts, scenes, corrections and exact-file visual reviews. `run/work/deck-review.json` records the assembled review. `run/work/native-edit-proof/` demonstrates editing the existing PowerPoint title and changing the research chart from 1,944 to 1,620 hours in a copy. The official scenario remains unchanged.

`run/bundle/deck-scenes.json` is the portable scene manifest. `examples/rebuild.py` repeats measurement and native construction from the frozen accepted targets and authored maps. This reconstruction was re-run in an isolated home, and all five actual previews were pixel-identical at the same 160 DPI in the recorded macOS LibreOffice environment. Image generation remains a creative step.

The source archive retains both the portable scenes and complete authoring evidence. The project page presents a single PowerPoint download action. PDF and source files remain available in the repository for maintainers.

The previous Consulting revision is preserved in the development workspace at `output/showcase-revisions/consulting-v2-at-replacement`. The personal Editorial presentation is unchanged.
''')
subprocess.run([sys.executable,str(repo/'docs/site/extract_objects.py'),'--manifest',str(case/'showcase.json')],check=True)
# Keep the archive self-contained without recursively including itself.
with zipfile.ZipFile(case/'deliverables/source-bundle.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted((case/'run').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(case))
 z.write(case/'README.md','README.md')
record={'schema_version':'1.0','revision':3,'pptx_sha256':hashlib.sha256((case/'deliverables/presentation.pptx').read_bytes()).hexdigest(),'body_canvas_px':[1920,960],'full_slide_px':[1920,1080],'all_five_reconstructed_via_packaged_runtime':True,'public_download':'PowerPoint only','source_archive_sha256':hashlib.sha256((case/'deliverables/source-bundle.zip').read_bytes()).hexdigest()}
(case/'publication.json').write_text(json.dumps(record,indent=2)+'\n')
archive=r.parent/'consulting-v2-at-replacement';assert not archive.exists()
# Every prepared artifact exists before replacing the currently viewed directory.
for s in m['slides']:
 for key in ['target','render','evidence','scene','objects']:assert(case/s[key]).is_file(),s[key]
live.rename(archive)
try:case.rename(live)
except BaseException:archive.rename(live);raise
print(json.dumps({'published_local_case':str(live),'preserved_revision':str(archive),**record},indent=2))
