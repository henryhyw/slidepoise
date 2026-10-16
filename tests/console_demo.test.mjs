import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('the installed Console uses the product system icon', () => {
  const html = readFileSync(new URL('../webapp/console/index.html', import.meta.url), 'utf8');
  const systemButton = html.match(/<button class="nav-item" data-view="system">([\s\S]*?)<\/button>/)?.[1] || '';
  assert.match(systemButton, /<svg viewBox="0 0 18 18"/);
  assert.doesNotMatch(systemButton, /⚙/);
});

test('the project showcase points to the only maintained website', () => {
  const html = readFileSync(new URL('../docs/site/index.html', import.meta.url), 'utf8');
  assert.match(html, /location\.replace/);
  assert.match(html, /https:\/\/www\.henryw\.me\/slidepoise\/docs\/site\//);
  assert.match(html, /location\.search \+ location\.hash/);
});
