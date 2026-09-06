#!/usr/bin/env python3
"""Build a borderless source board and deterministic manifest for novel illustrations."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from raster_decisions import illustration_decisions


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def clamp(box, w, h):
    x,y,bw,bh=[int(round(float(v))) for v in box]
    x=max(0,min(w-1,x)); y=max(0,min(h-1,y)); bw=max(1,min(w-x,bw)); bh=max(1,min(h-y,bh))
    return [x,y,bw,bh]


def fit_slot(cell, ratio):
    x,y,w,h=cell
    fw=min(w,h*ratio); fh=fw/ratio
    return [round(x+(w-fw)/2),round(y+(h-fh)/2),round(fw),round(fh)]


def choose_layout(ratios, W, H, margin, gutter):
    n=len(ratios); best=None
    for cols in range(1,min(4,n)+1):
        rows=math.ceil(n/cols)
        cell_w=(W-2*margin-(cols-1)*gutter)/cols
        cell_h=(H-2*margin-(rows-1)*gutter)/rows
        if cell_w<=1 or cell_h<=1: continue
        slots=[]; area=0.0
        for i,r in enumerate(ratios):
            row=i//cols; col=i%cols
            cell=[margin+col*(cell_w+gutter),margin+row*(cell_h+gutter),cell_w,cell_h]
            slot=fit_slot(cell,max(0.05,float(r))); slots.append(slot); area+=slot[2]*slot[3]
        score=area - rows*cols*0.01
        if best is None or score>best[0]: best=(score,slots,cols,rows)
    if best is None: raise ValueError('Unable to lay out illustration board')
    return best[1],best[2],best[3]


def font(size=24,bold=False):
    candidates=[Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf')]
    for p in candidates:
        if p.is_file(): return ImageFont.truetype(str(p),size=size)
    return ImageFont.load_default()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--image',type=Path,required=True)
    ap.add_argument('--semantic-map',type=Path,required=True)
    ap.add_argument('--config',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,required=True)
    ap.add_argument('--board',type=Path,required=True)
    ap.add_argument('--review-board',type=Path,required=True)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--brief',type=Path,required=True)
    args=ap.parse_args()
    semantic=load(args.semantic_map); config=load(args.config)
    refcfg=(config.get('generation',{}) or {}).get('illustration_refinement',{}) or {}
    W,H=[int(v) for v in refcfg.get('board_max_size_px',[2048,2048])]
    margin=int(refcfg.get('board_outer_margin_px',80)); gutter=int(refcfg.get('board_gutter_px',72))
    source=Image.open(args.image).convert('RGB'); sw,sh=source.size
    candidates=[]
    for e, decision in illustration_decisions(semantic):
        if decision['action']=='refine':
            box=e.get('bbox_hint') or e.get('bbox')
            if not (isinstance(box,list) and len(box)==4): raise SystemExit(f"{e.get('id')}: novel illustration missing bbox_hint")
            if Path(str(e['id'])).name != str(e['id']) or str(e['id']) in {'.', '..'}:
                raise ValueError('entity ID must be a safe filename')
            box=clamp(box,sw,sh); candidates.append((e,box))
    args.output_dir.mkdir(parents=True,exist_ok=True); (args.output_dir/'source-crops').mkdir(exist_ok=True)
    if not candidates:
        manifest={'source_image':str(args.image.resolve()),'board_dimensions_px':[W,H],'candidate_count':0,'items':[]}
        args.manifest.parent.mkdir(parents=True,exist_ok=True); args.manifest.write_text(json.dumps(manifest,indent=2)+'\n')
        args.brief.parent.mkdir(parents=True,exist_ok=True); args.brief.write_text('# No novel illustration refinement candidates\n')
        print(json.dumps({'candidate_count':0,'manifest':str(args.manifest.resolve())},indent=2)); return
    ratios=[b[2]/b[3] for _,b in candidates]
    slots,cols,rows=choose_layout(ratios,W,H,margin,gutter)
    board=Image.new('RGB',(W,H),'white'); items=[]
    for i,((e,box),slot) in enumerate(zip(candidates,slots),start=1):
        x,y,bw,bh=box; crop=source.crop((x,y,x+bw,y+bh)); crop_path=args.output_dir/'source-crops'/f"{e['id']}.png"; crop.save(crop_path)
        sx,sy,ssw,ssh=slot; resized=crop.resize((ssw,ssh),Image.Resampling.LANCZOS); board.paste(resized,(sx,sy))
        items.append({'entity_id':e['id'],'label':f'I{i:02d}','semantic_role':e.get('role'),'source_bbox_px':box,'source_aspect_ratio':round(bw/bh,6),'source_crop':str(crop_path.resolve()),'board_slot_px':slot,'board_slot_normalized':[round(sx/W,8),round(sy/H,8),round(ssw/W,8),round(ssh/H,8)]})
    args.board.parent.mkdir(parents=True,exist_ok=True); board.save(args.board)
    review=board.copy(); draw=ImageDraw.Draw(review); f=font(24,True)
    for item in items:
        x,y,w,h=item['board_slot_px']; draw.rectangle((x,y,x+w,y+h),outline=(230,70,20),width=3); draw.rectangle((x,y,x+64,y+34),fill='white'); draw.text((x+6,y+4),item['label'],fill='black',font=f)
    args.review_board.parent.mkdir(parents=True,exist_ok=True); review.save(args.review_board)
    manifest={'source_image':str(args.image.resolve()),'board_dimensions_px':[W,H],'layout':{'columns':cols,'rows':rows,'outer_margin_px':margin,'gutter_px':gutter},'candidate_count':len(items),'items':items}
    args.manifest.parent.mkdir(parents=True,exist_ok=True); args.manifest.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    profile=config.get('resolved_profile',{}) or {}; design=config.get('design',{}) or {}; av=(profile.get('hard_rules',{}) or {}).get('asset_vocabulary',{}) or {}; novel=av.get('novel_illustrations',{}) or {}
    brief=['# Illustration refinement brief','',f'Redraw the {len(items)} isolated illustration(s) from the attached borderless reference board.','Return one refined board with the same overall arrangement and the same per-item slot aspect ratios.','','## Hard rules','- Preserve each illustration\'s semantic meaning and recognizable subject.','- Improve small-scale artifacts, awkward details, and visual clarity; this is a focused redraw, not a new slide composition.','- Keep every illustration inside its corresponding reference-board slot and make it occupy that slot as fully as possible while preserving the source aspect ratio.','- Keep the whitespace gutters between slots empty.','- Do not add borders, frames, labels, IDs, captions, callouts, or cross-slot decorative composition.','- Do not merge illustrations or move one illustration into another slot.','- Preserve the local background behavior visible in each source crop unless doing so would create an obvious artifact.','- Match the approved slide/profile visual language.','','## Active profile guidance',f"Profile: {profile.get('name')} ({profile.get('profile_id')})",f"Novel illustration mode: {novel.get('mode','')}",f"Novel illustration guidance: {novel.get('guidance','')}",f"Style: {json.dumps(design.get('style',{}),ensure_ascii=False)}",'Visual principles:']
    brief += [f'- {v}' for v in profile.get('visual_principles',[])][:12]
    brief += ['','## Slot semantics']
    for item in items: brief.append(f"- {item['label']} / {item['entity_id']}: role={item.get('semantic_role')}; aspect_ratio={item['source_aspect_ratio']}; board_slot_normalized={item['board_slot_normalized']}")
    args.brief.parent.mkdir(parents=True,exist_ok=True); args.brief.write_text('\n'.join(brief)+'\n',encoding='utf-8')
    print(json.dumps({'candidate_count':len(items),'board':str(args.board.resolve()),'review_board':str(args.review_board.resolve()),'manifest':str(args.manifest.resolve()),'brief':str(args.brief.resolve())},indent=2,ensure_ascii=False))
if __name__=='__main__': main()
