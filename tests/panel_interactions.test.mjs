import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

function harness() {
  const nodes = new Map(), listeners = new Map();
  const node = selector => {
    if (!nodes.has(selector)) {
      const classes = new Set();
      nodes.set(selector, {
        innerHTML: '', textContent: '', hidden: false, dataset: {}, open: false,
        addEventListener() {}, showModal() { this.open = true; }, close() { this.open = false; },
        classList: { remove: value => classes.delete(value), toggle(value) { if (classes.has(value)) { classes.delete(value); return false; } classes.add(value); return true; }, contains: value => classes.has(value) },
      });
    }
    return nodes.get(selector);
  };
  const document = {
    hidden: false, activeElement: null,
    querySelector: selector => selector === 'dialog[open]' ? [...nodes.values()].find(item => item.open) : node(selector),
    querySelectorAll: () => [],
    addEventListener(type, fn) { if (!listeners.has(type)) listeners.set(type, []); listeners.get(type).push(fn); },
  };
  const context = vm.createContext({ document, setTimeout: () => 1, clearTimeout() {}, URLSearchParams });
  for (const file of ['app.js', 'authoring.js', 'session-panel.js']) vm.runInContext(readFileSync(new URL(`../webapp/ui/${file}`, import.meta.url), 'utf8'), context);
  return { context, document, node, listeners, run: code => vm.runInContext(code, context) };
}

function presentation() {
  return {
    path: '/presentations/strategy', name: 'Strategy <review>', overrides_revision: 'revision-1',
    overrides: {}, resolved_config: { resolved_profile: { name: 'Consulting', purpose: 'Make the decision clear' } },
    values: { density: 'balanced', display_font: 'Georgia', body_font: 'Arial', primary: '#111111', secondary: '#222222', highlight: '#333333', surface: '#eeeeee' },
    densities: { balanced: 'Balanced', spacious: 'Spacious' }, fonts: ['Georgia', 'Arial'],
    selected_sets: { icons: [], components: [] },
  };
}

test('bound presentation renders scoped editing actions and escaped asset names', () => {
  const h = harness();
  h.context.presentation = presentation();
  h.run(`state.run=presentation;sessionSnapshot={materials:[{name:'Client <draft>.pdf',url:'/api/artifact?path=client.pdf',size:2048}]};renderPanel()`);
  const html = h.node('#session-content').innerHTML;
  assert.match(html, /Strategy &lt;review&gt;/);
  assert.match(html, /Client &lt;draft&gt;\.pdf/);
  assert.equal((html.match(/data-session="true"/g) || []).length, 4);
  assert.deepEqual([...html.matchAll(/data-edit="([^"]+)"/g)].map(match => match[1]), ['guidance', 'typography', 'visual', 'libraries']);
  assert.match(html, /id="session-assets" type="file" multiple/);
  assert.match(html, /id="reset-run-style"/);
});

test('disconnected or moved presentation does not render writable controls', () => {
  const h = harness();
  for (const missing of [null, 'Folder moved']) {
    h.context.missing = missing;
    h.run('state.run=null;state.missingRun=missing;renderPanel()');
    const html = h.node('#session-content').innerHTML;
    assert.match(html, /<h1>.+<\/h1>/);
    assert.doesNotMatch(html, /<button|<input|data-edit=/);
  }
});

test('editing presentation typography sends only changed values with the current revision', async () => {
  const h = harness();
  h.context.presentation = presentation();
  const writes = [];
  h.context.saveRequest = async (path, body) => {
    writes.push({ path, body: JSON.parse(JSON.stringify(body)) });
    return { ...presentation(), overrides_revision: 'revision-2' };
  };
  h.run('state.run=presentation;api=saveRequest;renderRun=async()=>{};toast=()=>{}');
  await h.run("openStyleEditor('typography',true)");
  await h.run("saveEditor(new Map([['display_font','Georgia'],['body_font','Courier New']]))");
  assert.deepEqual(writes, [{ path: '/api/run/design', body: {
    run: '/presentations/strategy', values: { body_font: 'Courier New' }, revision: 'revision-1',
  } }]);
  assert.equal(h.run('state.run.overrides_revision'), 'revision-2');
});

test('style surface identifies inherited and overridden values', () => {
  const h = harness();
  h.run(`state.run={overrides:{design_overrides:{style:{density:'spacious'}}}};
    var payload={values:{density:'spacious',display_font:'Georgia',body_font:'Arial',primary:'#111111',secondary:'#222222',highlight:'#333333',surface:'#eeeeee'},densities:{spacious:'Spacious'},style_agency:{density:'guided',typography:'guided',palette:'guided'},selected_sets:{icons:[],components:[]}}`);
  const cards = h.run('styleCards(payload,true)');
  assert.equal((cards.match(/Changed for this presentation/g) || []).length, 1);
  assert.equal((cards.match(/Using the saved profile/g) || []).length, 3);
});

test('refresh waits while a settings editor is active', async () => {
  const h = harness();
  h.run("state.run={path:'/run'};var calls=0;api=async()=>{calls++;return {}};");
  h.node('#editor-dialog').open = true;
  await h.run('refreshPanel(true)');
  assert.equal(h.run('calls'), 0);
  h.node('#editor-dialog').open = false;
  h.document.activeElement = { matches: selector => selector.includes('input') };
  await h.run('refreshPanel(true)');
  assert.equal(h.run('calls'), 0);
});

test('pending changes explain adoption timing without workflow progress', () => {
  const h = harness();
  h.run("sessionSnapshot={pending_events:{events:[{id:'one'}]}};");
  const message = h.run('pendingChanges()');
  assert.match(message, /1 change saved/);
  assert.match(message, /next affected operation/);
  assert.doesNotMatch(message, /Stage progress|approval/);
});
