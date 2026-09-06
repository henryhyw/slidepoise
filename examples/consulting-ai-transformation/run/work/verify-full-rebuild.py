import hashlib,json,zipfile
from pathlib import Path
from PIL import Image,ImageChops
w=Path(__file__).resolve().parent;r=w.parent;repo=r.parents[2];rebuilt=repo/'output/product-qa-v3/consulting-full-rebuild'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
comparisons=[]
for i in range(1,6):
 a=r/f'preview/slide-{i:03d}.png';b=rebuilt/f'preview160/slide-{i:03d}.png';x=Image.open(a).convert('RGB');y=Image.open(b).convert('RGB');same=x.size==y.size and ImageChops.difference(x,y).getbbox() is None
 comparisons.append({'page':i,'reference_sha256':sha(a),'rebuilt_sha256':sha(b),'dimensions':list(x.size),'pixels_identical':same})
with zipfile.ZipFile(r/'deliverables/presentation.pptx') as original,zipfile.ZipFile(rebuilt/'deliverables/presentation.pptx') as current:
 parts=[n for n in original.namelist() if n.endswith('.xml') and n.startswith(('ppt/slides/slide','ppt/slideLayouts/slideLayout','ppt/slideMasters/slideMaster','ppt/charts/chart','ppt/notesSlides/notesSlide'))]
 native=[{'part':n,'identical':original.read(n)==current.read(n)} for n in parts]
d={'schema_version':'1.0','method':'examples/rebuild.py with accepted targets, host semantic maps and reconstruction handoffs. Re-resolved repository configuration in an isolated home, then OpenCV measurement, contract compilation and native deck construction. Both actual LibreOffice renders use 160 DPI.','source_pptx_sha256':sha(r/'deliverables/presentation.pptx'),'rebuilt_pptx_sha256':sha(rebuilt/'deliverables/presentation.pptx'),'render_comparisons':comparisons,'native_xml_comparisons':native,'frozen_input_bindings':json.loads((rebuilt/'rebuild.json').read_text())['input_files'],'preview_environment_scope':'Recorded macOS LibreOffice and fonts. This establishes reproducibility of frozen reconstruction inputs, not deterministic image generation.'}
(w/'rebuild-verification.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'all_pages_pixel_identical':all(x['pixels_identical'] for x in comparisons),'all_native_parts_identical':all(x['identical'] for x in native),'parts':len(native)},indent=2))
assert all(x['pixels_identical'] for x in comparisons)
