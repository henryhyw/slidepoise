import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const source = readFileSync(new URL('../webapp/console/app.js', import.meta.url), 'utf8');
function harness() {
  const nodes = new Map();
  const node = selector => {
    if (!nodes.has(selector)) nodes.set(selector, {
      innerHTML: '', textContent: '', hidden: false, dataset: {}, attributes: {},
      addEventListener() {}, remove() {},
      setAttribute(key, value) { this.attributes[key] = value; },
      removeAttribute(key) { delete this.attributes[key]; },
    });
    return nodes.get(selector);
  };
  const controls = ['a', 'b'].map(id => ({ ...node(id), dataset: { profileDefault: id } }));
  const context = vm.createContext({
    document: {
      querySelector: selector => selector === 'dialog[open]' ? [...nodes.values()].find(n => n.open) : node(selector),
      querySelectorAll: selector => selector === '[data-profile-default]' ? controls : [],
      addEventListener() {},
    },
    fetch: () => new Promise(() => {}),
    setTimeout: () => 1, clearTimeout() {},
  });
  vm.runInContext(source, context);
  vm.runInContext("state.overview = {active_profile:'a'}; state.view='design'; toast=()=>{}; refreshOverview=async()=>{}; loadDesign=async()=>{};", context);
  return { context, controls, node, run: code => vm.runInContext(code, context) };
}

test('default selection prevents overlapping writes and restores controls', async () => {
  const h = harness();
  let finish;
  let writes = 0;
  h.context.saveRequest = async () => { writes++; await new Promise(resolve => { finish = resolve; }); };
  h.run('api = saveRequest');
  const pending = h.run("selectDefaultProfile('b')");
  assert.equal(h.controls[1].textContent, 'Applying…');
  assert.ok(h.controls.every(control => control.disabled));
  await h.run("selectDefaultProfile('b')");
  assert.equal(writes, 1);
  h.run("state.overview.active_profile='b'");
  finish();
  await pending;
  assert.equal(h.run('state.defaultSaving'), false);
  assert.equal(h.controls[0].disabled, false);
  assert.equal(h.controls[1].disabled, true);
});

test('failed default selection leaves the old default and remains retryable', async () => {
  const h = harness();
  h.context.saveRequest = async () => { throw new Error('offline'); };
  h.run('api = saveRequest');
  await assert.rejects(h.run("selectDefaultProfile('b')"), /offline/);
  assert.equal(h.run('state.overview.active_profile'), 'a');
  assert.equal(h.run('state.defaultSaving'), false);
  assert.equal(h.controls[1].disabled, false);
  assert.equal(h.controls[1].attributes['aria-busy'], undefined);
});

test('system loads the supported tools and opens named, bounded detail views', async () => {
  const h = harness();
  const dialog = h.node('#preview-dialog');
  dialog.showModal = () => { dialog.open = true; };
  const names = ['Python', 'OpenCV', 'Node', 'PptxGenJS', 'LibreOffice', 'Poppler'];
  h.context.systemRequest = async path => {
    if (path === '/api/settings') return { config: {}, revision: 'current' };
    if (path === '/api/health') return names.map(name => ({ name, available: true, detail: 'Installed' }));
    throw new Error(`Unexpected system request ${path}`);
  };
  h.run('api = systemRequest');
  await h.run('loadSystem()');
  for (const name of names) {
    h.run(`openCapability(${JSON.stringify(name)})`);
    assert.equal(h.node('#preview-title').textContent, name);
    assert.ok(h.node('#preview-body').innerHTML.includes('capability-detail'));
    assert.equal(dialog.open, true);
    dialog.open = false;
  }
});

test('shared Agent changes refresh Console without overwriting an open editor', async () => {
  const h = harness();
  h.run(`var loads=0;state.overview.profiles=[{id:'a'}];state.consoleProfile='a';
    api=async()=>({revision:'changed'});loadDesign=async()=>loads++;`);
  h.node('#editor-dialog').open=true;
  await h.run('refreshSharedFiles()');
  assert.equal(h.run('loads'), 0);
  h.node('#editor-dialog').open=false;
  await h.run('refreshSharedFiles()');
  assert.equal(h.run('loads'), 1);
  await h.run('refreshSharedFiles()');
  assert.equal(h.run('loads'), 1);
});
