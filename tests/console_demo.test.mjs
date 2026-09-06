import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
function demo() {
  const context = vm.createContext({window: {}, structuredClone, URL});
  vm.runInContext(readFileSync(new URL('../docs/site/console-demo/fixtures.js', import.meta.url), 'utf8'), context);
  vm.runInContext(readFileSync(new URL('../docs/site/console-demo/adapter.js', import.meta.url), 'utf8'), context);
  return context.window.consoleDemoAPI;
}
test('Console demo saves independently, rejects stale edits and resets with a new page', async () => {
  const first=demo(), second=demo();
  const original=await first('/api/design?profile=consulting');
  await first('/api/profile/style',{profile:'consulting', revision:original.revision, values:{body_font:'Courier New'}, profile_values:{style_agency:{typography:'guided'}}});
  assert.equal((await first('/api/design?profile=consulting')).values.body_font,'Courier New');
  assert.equal((await second('/api/design?profile=consulting')).values.body_font,original.values.body_font);
  await assert.rejects(first('/api/profile/style',{profile:'consulting',revision:original.revision,values:{body_font:'Arial'}}),/changed/);
  assert.equal((await demo()('/api/design?profile=consulting')).values.body_font,original.values.body_font);
  await assert.rejects(first('/api/component/open',{id:'any'}),/installed Console/);
});

test('Console uses its own system icon on every surface', () => {
  for (const file of ['../webapp/console/index.html', '../docs/site/console-demo/index.html']) {
    const html = readFileSync(new URL(file, import.meta.url), 'utf8');
    const systemButton = html.match(/<button class="nav-item" data-view="system">([\s\S]*?)<\/button>/)?.[1] || '';
    assert.match(systemButton, /<svg viewBox="0 0 18 18"/);
    assert.doesNotMatch(systemButton, /⚙/);
  }
});
