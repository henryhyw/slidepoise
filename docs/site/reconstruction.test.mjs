import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {reconstructionItems,createReconstructionViewer} from './reconstruction-viewer.mjs';
const semantic={entities:[{id:'title',kind:'text',bbox_hint:[10,10,80,20]}],groups:[{id:'g',children:['title']}]};
const measurement={source:{width_px:100,height_px:100},entities:[{id:'title',measurement:{visible_bbox:{px:[12,13,66,14]}}}]};
test('interpretation keeps authored allocation separate from measured visible ink',()=>{
  const data=reconstructionItems(semantic,measurement);
  assert.deepEqual(data.entities[0].planned,[10,10,80,20]);
  assert.deepEqual(data.entities[0].measured,[12,13,66,14]);
  assert.throws(()=>reconstructionItems(semantic,{...measurement,entities:[]}),/no measurement/);
  assert.throws(()=>reconstructionItems({...semantic,groups:[{children:['missing']}]},measurement),/inconsistent/);
});
test('all retained sample pages expose matching interpretation and measurement records',()=>{
  for(const name of ['consulting-ai-transformation','personal-thinking-system']) {
    const base=new URL(`../../examples/${name}/`,import.meta.url);
    const read=path=>JSON.parse(readFileSync(new URL(path,base),'utf8'));
    for(const slide of read('showcase.json').slides) {
      const data=reconstructionItems(read(slide.semantic),read(slide.measurement));
      assert.ok(data.entities.length>0);
      assert.ok(data.entities.every(item=>item.planned?.length===4));
    }
  }
});
test('changing a slide aborts prior reconstruction requests before they can replace its view',async()=>{
  const previous=globalThis.document;
  globalThis.document={createElement:()=>({className:'',textContent:''})};
  const region=()=>({hidden:true,children:[],replaceChildren(...items){this.children=items;},append(...items){this.children.push(...items);}});
  const layer=region(),panel=region(),requests=[];
  const viewer=createReconstructionViewer({layer,panel,positionLayer:()=>{},fetchJSON:(url,signal)=>new Promise(resolve=>requests.push({url,signal,resolve}))});
  const old=viewer.show({semantic:'old-s',measurement:'old-m'},'semantic',null);
  viewer.clear();
  assert.ok(requests.every(item=>item.signal.aborted));
  requests[0].resolve(semantic);requests[1].resolve(measurement);
  await old;
  assert.equal(panel.hidden,true);
  assert.equal(layer.children.length,0);
  globalThis.document=previous;
});
