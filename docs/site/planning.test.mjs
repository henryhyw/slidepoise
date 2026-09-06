import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createPlanView } from './planning-viewer.mjs';

class Element extends EventTarget {
  constructor(tagName) {
    super();
    this.tagName = tagName;
    this.children = [];
    this.attributes = new Map();
    this.parentElement = null;
    this.className = '';
    this.ownText = '';
  }
  set textContent(value) { this.replaceChildren(); this.ownText = String(value); }
  get textContent() { return this.ownText + this.children.map(child => child.textContent).join(' '); }
  get isConnected() { return this.root === true || this.parentElement?.isConnected === true; }
  get lastElementChild() { return this.children.at(-1); }
  get childElementCount() { return this.children.length; }
  getBoundingClientRect() { return this.bounds || { top: 0, bottom: 40 }; }
  append(...children) {
    for (const child of children) { child.parentElement = this; this.children.push(child); }
  }
  replaceChildren(...children) {
    for (const child of this.children) child.parentElement = null;
    this.children = [];
    this.ownText = '';
    this.append(...children);
  }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  getAttribute(name) { return this.attributes.get(name); }
  click() { this.dispatchEvent(new Event('click')); }
}

function descendants(root, predicate) {
  return root.children.flatMap(child => [
    ...(predicate(child) ? [child] : []), ...descendants(child, predicate),
  ]);
}
const byClass = (root, name) => descendants(root, node => node.className.split(' ').includes(name));
const settle = () => new Promise(resolve => setImmediate(resolve));
const normalize = value => String(value).replace(/\s+/g, ' ').trim();

function contentValues(value) {
  if (Array.isArray(value)) return value.flatMap(contentValues);
  if (value && typeof value === 'object') {
    return Object.entries(value).filter(([key]) => key !== 'role').flatMap(([, item]) => contentValues(item));
  }
  return value === null || value === undefined ? [] : [normalize(value)];
}

function assertFullContent(detail, intent) {
  const brief = byClass(detail, 'slide-plan')[0];
  assert.ok(brief, 'The selected page has a full brief');
  const content = byClass(brief, 'plan-blocks')[0];
  const visible = normalize(content.textContent);
  for (const value of contentValues(intent.required_content)) {
    assert.ok(visible.includes(value), `Required source content is missing: ${value}`);
  }
}

test('plan navigation preserves complete source content, isolates slide selection and rejects stale or missing input', async t => {
  const previous = { document: globalThis.document, Image: globalThis.Image,
    requestAnimationFrame: globalThis.requestAnimationFrame };
  const body = new Element('body');
  body.root = true;
  body.scrollTop = 900;
  const frames = [];
  globalThis.document = { createElement: tag => new Element(tag), body };
  globalThis.Image = class extends Element { constructor() { super('img'); } };
  globalThis.requestAnimationFrame = callback => frames.push(callback);
  t.after(() => {
    globalThis.document = previous.document;
    globalThis.Image = previous.Image;
    globalThis.requestAnimationFrame = previous.requestAnimationFrame;
  });

  const source = new URL('../../examples/consulting-ai-transformation/run/', import.meta.url);
  const outline = JSON.parse(readFileSync(new URL('work/deck-outline.json', source), 'utf8'));
  const ids = outline.slides.slice(0, 2).map(slide => slide.slide_id);
  const intents = ids.map(id => JSON.parse(readFileSync(new URL(`slides/${id}/work/slide-intent.json`, source), 'utf8')));
  const slides = ids.map(id => ({ id, thumbnail: `${id}.png`, planning: { inputs: [] } }));
  const requests = [];
  const shown = [];
  const announcements = [];
  const controller = new AbortController();
  const loadIntent = (slide, signal) => new Promise(resolve => requests.push({ slide, signal, resolve }));
  const view = createPlanView({ outline, slides, loadIntent, signal: controller.signal,
    onShowSlide: slide => shown.push(slide.id), announce: value => announcements.push(value) });
  body.append(view);
  const navigation = byClass(view, 'plan-page-option');
  const detail = byClass(view, 'plan-detail')[0];

  navigation[1].click();
  assert.equal(requests[0].signal.aborted, true, 'A new selection cancels the earlier page fetch');
  requests[1].resolve(intents[1]);
  await settle();
  assert.equal(view.isConnected, true, 'Choosing a page keeps the plan in its container');
  assert.deepEqual(shown, [], 'Plan navigation does not navigate the presentation');
  assert.equal(navigation[1].getAttribute('aria-pressed'), 'true');
  assertFullContent(detail, intents[1]);
  assert.equal(descendants(detail, node => node.tagName === 'table').length, 3,
    'The chart values and both source tables remain available');
  const selectedContent = detail.textContent;
  requests[0].resolve(intents[0]);
  await settle();
  assert.equal(detail.textContent, selectedContent, 'A late first-page response cannot replace the selected page');

  navigation[0].click();
  requests[2].resolve(intents[0]);
  await settle();
  assertFullContent(detail, intents[0]);
  assert.deepEqual(shown, []);
  byClass(detail, 'plan-show-slide')[0].click();
  assert.deepEqual(shown, [ids[0]], 'Only the explicit show action requests presentation navigation');

  navigation[1].click();
  const closingContent = detail.textContent;
  const announcedBeforeClose = announcements.length;
  controller.abort();
  body.replaceChildren();
  assert.equal(requests[3].signal.aborted, true, 'Closing the view cancels its active page fetch');
  requests[3].resolve(intents[1]);
  await settle();
  assert.equal(detail.textContent, closingContent, 'A closed view ignores its late response');
  assert.equal(announcements.length, announcedBeforeClose);

  const retryRequests = [];
  const retryView = createPlanView({ outline, slides,
    loadIntent: () => new Promise(resolve => retryRequests.push(resolve)),
    onShowSlide: slide => shown.push(slide.id) });
  body.append(retryView);
  retryRequests[0]({ ...intents[0], required_content: [] });
  await settle();
  const retryDetail = byClass(retryView, 'plan-detail')[0];
  assert.equal(byClass(retryDetail, 'plan-error').length, 1, 'Missing full content is an explicit error');
  assert.equal(byClass(retryDetail, 'slide-plan').length, 0, 'An error is not replaced with a headline-only brief');
  assert.equal(retryDetail.getAttribute('aria-busy'), 'false');
  byClass(retryView, 'plan-page-option')[0].click();
  retryRequests[1](intents[0]);
  await settle();
  assertFullContent(retryDetail, intents[0]);

  const scrollContainer = new Element('div');
  scrollContainer.bounds = { top: 100, bottom: 400 };
  scrollContainer.scrollTop = 500;
  const scrollView = createPlanView({ outline, slides, scrollContainer,
    loadIntent: async slide => intents[ids.indexOf(slide.id)], onShowSlide: () => {} });
  scrollContainer.append(scrollView);
  body.append(scrollContainer);
  await settle();
  assert.equal(frames.length, 0, 'Initial loading preserves the presentation overview');
  assert.equal(scrollContainer.scrollTop, 500);
  byClass(scrollView, 'plan-page-option')[1].click();
  await settle();
  assert.equal(scrollContainer.scrollTop, 500, 'Selection waits for layout before adjusting scrolling');
  assert.equal(frames.length, 1);
  frames.shift()();
  assert.ok(scrollContainer.scrollTop < 500, 'An offscreen heading is brought back into its own scroll area');
  assert.equal(body.scrollTop, 900, 'Plan selection does not move the outer page');
});
