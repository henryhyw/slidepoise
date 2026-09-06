#!/usr/bin/env python3
"""Crop refined illustration slots from one returned refinement board."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from PIL import Image

def main():
 p=argparse.ArgumentParser(); p.add_argument('--image',type=Path,required=True); p.add_argument('--manifest',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--mapping',type=Path,required=True); a=p.parse_args()
 manifest=json.loads(a.manifest.read_text(encoding='utf-8')); image=Image.open(a.image).convert('RGBA'); W,H=image.size; expW,expH=manifest.get('board_dimensions_px',[W,H]); sx=W/expW; sy=H/expH; a.output_dir.mkdir(parents=True,exist_ok=True); items=[]
 for item in manifest.get('items',[]):
  x,y,w,h=item['board_slot_px']; box=[round(x*sx),round(y*sy),round((x+w)*sx),round((y+h)*sy)]; crop=image.crop(tuple(box)); out=a.output_dir/f"{item['entity_id']}.png"; crop.save(out); items.append({'entity_id':item['entity_id'],'refined_raster':str(out.resolve()),'source_aspect_ratio':item.get('source_aspect_ratio'),'output_crop_px':[box[0],box[1],box[2]-box[0],box[3]-box[1]]})
 mapping={'refined_board':str(a.image.resolve()),'actual_board_dimensions_px':[W,H],'items':items}; a.mapping.parent.mkdir(parents=True,exist_ok=True); a.mapping.write_text(json.dumps(mapping,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); print(json.dumps(mapping,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
