import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { existsSync, mkdtempSync, mkdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { chromium } from 'playwright';

const root = fileURLToPath(new URL('../../', import.meta.url));
const localPython = join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const python = process.env.SLIDEPOISE_TEST_PYTHON || (existsSync(localPython) ? localPython : 'python');

async function fixture(t, viewport) {
  const cleanup = [];
  t.after(async () => {
    const failures = [];
    for (const close of cleanup.reverse()) {
      try { await close(); } catch (error) { failures.push(error); }
    }
    if (failures.length) throw new AggregateError(failures, 'Browser fixture cleanup failed');
  });
  const directory = mkdtempSync(join(tmpdir(), 'slidepoise-browser-'));
  cleanup.push(() => rmSync(directory, { recursive: true, force: true }));
  // Serve the real application against disposable settings and a real presentation.
  const server = spawn(python, ['-u', '-c', `
import json, os
from pathlib import Path
from http.server import ThreadingHTTPServer
from framework.paths import BUNDLED_PROFILES_ROOT
from framework.profiles import initialize_home
from framework import sessions
from webapp.server import Handler
initialize_home(BUNDLED_PROFILES_ROOT)
run = sessions.create('Browser <review>', str(Path(os.environ['SLIDEPOISE_HOME']).parent / 'presentation'))
service = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
print(json.dumps({'url': 'http://127.0.0.1:' + str(service.server_port), 'run': str(run)}), flush=True)
service.serve_forever()
`], { cwd: root, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', SLIDEPOISE_HOME: join(directory, 'home') } });
  let serverLog = '';
  server.stderr.on('data', chunk => { serverLog += chunk; });
  cleanup.push(async () => {
    if (server.exitCode === null && server.signalCode === null) {
      const closed = once(server, 'close');
      server.kill();
      await closed;
    }
  });
  const lines = createInterface({ input: server.stdout });
  const connection = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Server startup timed out\n${serverLog}`)), 20_000);
    lines.once('line', line => { clearTimeout(timer); resolve(JSON.parse(line)); });
    server.once('error', error => { clearTimeout(timer); reject(error); });
    server.once('exit', code => { clearTimeout(timer); reject(new Error(`Server exited with ${code}\n${serverLog}`)); });
  });
  const browser = await chromium.launch();
  cleanup.push(() => browser.close());
  const context = await browser.newContext({ viewport });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();
  page.setDefaultTimeout(8_000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  cleanup.push(async () => {
    if (!t.passed) {
      const evidence = join(root, 'workspace/test-results/browser');
      mkdirSync(evidence, { recursive: true });
      const name = t.name.replace(/[^a-z0-9]+/gi, '-');
      await page.screenshot({ path: join(evidence, `${name}.png`), fullPage: true });
      await context.tracing.stop({ path: join(evidence, `${name}.zip`) });
    } else await context.tracing.stop();
    await context.close();
  });
  async function get(path) {
    const response = await context.request.get(connection.url + path);
    assert.equal(response.status(), 200, await response.text());
    return response.json();
  }
  return { ...connection, page, context, errors, get };
}

async function dismissBackdrop(page) {
  const dialog = page.locator('#editor-dialog');
  const box = await dialog.boundingBox();
  assert.ok(box && box.x > 0, 'The dialog must leave a reachable backdrop');
  // A drag out of the form must preserve the draft.
  await page.mouse.move(box.x + 8, box.y + 8);
  await page.mouse.down();
  await page.mouse.move(1, 1);
  await page.mouse.up();
  assert.equal(await dialog.isVisible(), true);
  await page.mouse.click(1, 1);
  await dialog.waitFor({ state: 'hidden' });
}

for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
  test(`Console saves settings and protects an open draft at ${viewport.width}px`, { timeout: 60_000 }, async t => {
    const h = await fixture(t, viewport);
    const { page } = h;
    await page.goto(h.url + '/console/#design');
    const profile = page.locator('[data-profile-default="editorial-archive"]');
    const saved = page.waitForResponse(r => r.url().endsWith('/api/profile') && r.request().method() === 'POST');
    await profile.click();
    assert.equal((await saved).status(), 200);
    assert.equal((await h.get('/api/context')).active_profile, 'editorial-archive');

    await page.locator('.nav-item[data-view="system"]').click();
    await page.locator('[data-capability="OpenCV"]').click();
    const details = page.locator('#preview-dialog');
    await details.waitFor({ state: 'visible' });
    assert.equal(await page.locator('#preview-title').textContent(), 'OpenCV');
    const bounds = await details.boundingBox();
    assert.ok(bounds.x >= 0 && bounds.y >= 0 && bounds.x + bounds.width <= viewport.width + 1 && bounds.y + bounds.height <= viewport.height + 1);
    assert.ok((await page.locator('#preview-body dd').allTextContents()).every(text => text.trim()));
    await details.getByRole('button', { name: 'Close', exact: true }).click();
    await page.locator('#edit-generation').click();
    await page.locator('input[name="mode"][value="manual"]').check();
    await page.locator('#editor-save').click();
    await page.locator('#editor-dialog').waitFor({ state: 'hidden' });
    assert.equal((await h.get('/api/generation')).values.mode, 'manual');
    await page.reload();
    await page.locator('#edit-generation').click();
    assert.equal(await page.locator('input[value="manual"]').isChecked(), true);

    // Another writer changes the same file after this editor captured its revision.
    const current = await h.get('/api/generation');
    const external = await h.context.request.post(h.url + '/api/generation', {
      data: { values: { ...current.values, mode: 'auto' }, revision: current.revision },
    });
    assert.equal(external.status(), 200, await external.text());
    await page.locator('[name="instructions"]').fill('Keep this draft');
    await page.locator('#editor-save').click();
    await page.locator('#editor-error').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#editor-dialog').isVisible(), true);
    assert.equal(await page.locator('[name="instructions"]').inputValue(), 'Keep this draft');
    assert.equal((await h.get('/api/generation')).values.mode, 'auto');
    await dismissBackdrop(page);
    assert.deepEqual(h.errors, []);
  });

  test(`Panel edits stay within the presentation at ${viewport.width}px`, { timeout: 60_000 }, async t => {
    const h = await fixture(t, viewport);
    const { page } = h;
    const before = await h.get('/api/settings');
    await page.goto(h.url + '/?run=' + encodeURIComponent(h.run));
    const guidance = page.locator('[data-edit="guidance"] .inheritance');
    const typography = page.locator('[data-edit="typography"] .inheritance');
    const inherited = await guidance.textContent();
    assert.equal(await typography.textContent(), inherited);
    await page.locator('[data-edit="typography"]').click();
    await page.locator('[name="body_font"]').fill('Courier New');
    await page.locator('#editor-save').click();
    await page.locator('#editor-dialog').waitFor({ state: 'hidden' });
    await page.waitForFunction(() => !document.querySelector('#editor-save').disabled);
    const run = await h.get('/api/run?path=' + encodeURIComponent(h.run));
    assert.equal(run.values.body_font, 'Courier New');
    assert.deepEqual(await h.get('/api/settings'), before);
    assert.equal(await guidance.textContent(), inherited);
    assert.notEqual(await typography.textContent(), inherited);
    await page.reload();
    await page.locator('[data-edit="typography"]').click();
    assert.equal(await page.locator('[name="body_font"]').inputValue(), 'Courier New');
    await dismissBackdrop(page);

    await page.locator('#session-assets').setInputFiles({
      name: 'Client <draft>.txt', mimeType: 'text/plain', buffer: Buffer.from('Source material'),
    });
    const asset = page.getByRole('link', { name: /Client <draft>\.txt/ });
    await asset.waitFor({ state: 'visible' });
    const response = await h.context.request.get(h.url + await asset.getAttribute('href'));
    assert.equal(await response.text(), 'Source material');
    assert.deepEqual(h.errors, []);
  });
}
