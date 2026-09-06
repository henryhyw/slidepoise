#!/usr/bin/env python3
"""Attach refined raster paths to host-authored novel-illustration semantic entities."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from raster_decisions import illustration_decisions

def main():
 p=argparse.ArgumentParser(); p.add_argument('--semantic-map',type=Path,required=True); p.add_argument('--mapping',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
 semantic=json.loads(a.semantic_map.read_text(encoding='utf-8')); mapping=json.loads(a.mapping.read_text(encoding='utf-8')); by={str(i['entity_id']):i for i in mapping.get('items',[])}; updated=[]
 selected={str(e['id']) for e,d in illustration_decisions(semantic) if d['action']=='refine'}
 if not set(by).issubset(selected): raise SystemExit('Refinement mapping includes objects not selected by the host')
 for e in semantic.get('entities',[]):
  eid=str(e.get('id')); rec=by.get(eid)
  if rec:
   if not (e.get('kind')=='image' and e.get('visual_source_class')=='novel_illustration'): raise SystemExit(f'{eid}: refinement mapping may only target image/novel_illustration entities')
   path=Path(rec['refined_raster']);
   if not path.is_file(): raise SystemExit(f'{eid}: refined raster missing: {path}')
   e['raster_source_override']=str(path.resolve()); e['raster_fit']='contain'; e['illustration_refinement_status']='refined'; updated.append(eid)
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(semantic,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); print(json.dumps({'updated_entity_ids':updated,'output':str(a.output.resolve())},indent=2))
if __name__=='__main__': main()
