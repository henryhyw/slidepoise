import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';

const source = readFileSync(new URL('../webapp/ui/dialog-dismiss.js', import.meta.url), 'utf8');
function harness() {
  const listeners = {};
  const listen = (name, handler) => { listeners[name] = handler; };
  vm.runInNewContext(source, { document: { addEventListener: listen }, window: { addEventListener: listen } });
  const makeDialog = () => ({
    open: true, closes: 0,
    getBoundingClientRect: () => ({ left: 100, top: 100, right: 400, bottom: 400 }),
    close() { this.open = false; this.closes++; listeners.close(); },
  });
  const dialog = makeDialog();
  const fire = (type, x = 50, y = 50, options = {}) => {
    const targetDialog = options.dialog || dialog;
    const event = { clientX: x, clientY: y, pointerId: 1, button: 0, isPrimary: true, detail: 1,
      target: { closest: () => targetDialog.open ? targetDialog : null },
      preventDefault() { this.prevented = true; },
      stopImmediatePropagation() { this.stopped = true; }, ...options };
    listeners[type](event);
    return event;
  };
  return { dialog, makeDialog, fire };
}

test('outside press and release dismiss once and consume the click', () => {
  const h = harness();
  h.fire('pointerdown'); h.fire('pointerup');
  assert.equal(h.dialog.open, true);
  const click = h.fire('click');
  assert.equal(h.dialog.closes, 1);
  assert.ok(click.prevented && click.stopped);
});

for (const [name, down, up] of [
  ['inside to outside', 200, 50], ['outside to inside', 50, 200],
  ['inside to inside', 200, 200], ['dialog padding and border', 100, 100],
]) test(name + ' keeps the dialog open', () => {
  const h = harness();
  h.fire('pointerdown', down, down); h.fire('pointerup', up, up); h.fire('click', up, up);
  assert.equal(h.dialog.open, true);
});

for (const event of ['pointercancel', 'blur', 'close']) test(event + ' cancels an outside gesture', () => {
  const h = harness();
  h.fire('pointerdown'); h.fire(event); h.fire('pointerup'); h.fire('click');
  assert.equal(h.dialog.open, true);
});

test('ignores right clicks, secondary pointers, mismatched releases and keyboard clicks', () => {
  for (const [down, up, click] of [
    [{ button: 2 }, { button: 2 }, {}], [{ isPrimary: false }, {}, {}],
    [{}, { pointerId: 2 }, {}], [{}, {}, { detail: 0 }],
  ]) {
    const h = harness();
    h.fire('pointerdown', 50, 50, down); h.fire('pointerup', 50, 50, up); h.fire('click', 50, 50, click);
    assert.equal(h.dialog.open, true);
  }
});

test('only the targeted top dialog closes', () => {
  const h = harness(), upper = h.makeDialog();
  for (const type of ['pointerdown', 'pointerup', 'click']) h.fire(type, 50, 50, { dialog: upper });
  assert.equal(upper.open, false);
  assert.equal(h.dialog.open, true);
});

test('changing dialogs during a gesture cannot dismiss either', () => {
  const h = harness(), upper = h.makeDialog();
  h.fire('pointerdown'); h.fire('pointerup', 50, 50, { dialog: upper }); h.fire('click', 50, 50, { dialog: upper });
  assert.ok(h.dialog.open && upper.open);
});

test('Console and Panel both load the shared dismissal behavior', () => {
  for (const surface of ['ui', 'console']) {
    const html = readFileSync(new URL(`../webapp/${surface}/index.html`, import.meta.url), 'utf8');
    assert.match(html, /<script src="\/dialog-dismiss\.js"><\/script>/);
  }
});
