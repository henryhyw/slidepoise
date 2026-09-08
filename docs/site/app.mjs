import { createObjectInspector, validateObjectDocument } from './object-inspector.mjs';
import { createReconstructionViewer } from './reconstruction-viewer.mjs';
import { createPlanView, createSlideBrief } from './planning-viewer.mjs';

const byId = (id) => document.getElementById(id);
const state = {
  decks: [], deck: null, slideIndex: 0, mode: 'rebuilt', inspectorOpen: false,
  objectStatus: 'empty', objectCount: 0, artifactRequest: 0, artifactFetch: null,
  artifactTrigger: null, artifactMotion: null, viewerScroll: null, walkthrough: null, objectLoad: null,
};

function announce(message) { byId('announcement').textContent = message; }
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function setInspectorOpen(open) {
  state.inspectorOpen = Boolean(open && state.mode === 'rebuilt');
  byId('object-panel').hidden = !state.inspectorOpen;
  byId('studio-workspace').dataset.inspector = state.inspectorOpen ? 'open' : 'closed';
  byId('object-toggle').setAttribute('aria-expanded', String(state.inspectorOpen));
}

function updateObjectStatus() {
  byId('object-count').textContent = String(state.objectCount);
  byId('object-count').hidden = !state.objectCount;
  byId('object-toggle').disabled = state.mode !== 'rebuilt' || state.objectStatus !== 'ready' || !state.objectCount;
  const help = state.mode === 'semantic' ? 'Agent interpretation' : state.mode === 'measurements' ? 'Measured from the generated image' : state.mode === 'compare'
    ? 'Drag to compare both versions'
    : state.mode === 'target'
      ? 'AI-generated image'
      : state.objectStatus === 'loading'
        ? 'Loading native objects…'
        : state.objectStatus === 'ready' && state.objectCount
          ? 'Read-only · Select an object'
          : 'Read-only PowerPoint preview';
  byId('viewer-mode-help').textContent = help;
}

const inspector = createObjectInspector({
  surface: byId('slide-surface'), panel: byId('object-panel'), announce,
  onSelectionChange: (item) => { if (item) setInspectorOpen(true); },
  onStateChange: ({ status, objectCount }) => {
    state.objectStatus = status;
    state.objectCount = objectCount;
    updateObjectStatus();
  },
});

function artifactURL(value, manifestURL) {
  if (value == null) return null;
  if (typeof value !== 'string' || !value.trim() || value.startsWith('/') || /^[a-z][a-z\d+.-]*:/i.test(value)) {
    throw new Error('Artifact paths must be relative to their example.');
  }
  const directory = new URL('.', manifestURL);
  const resolved = new URL(value, directory);
  if (resolved.origin !== directory.origin || !resolved.pathname.startsWith(directory.pathname) || resolved.search || resolved.hash) {
    throw new Error('An artifact path leaves its example directory.');
  }
  return resolved.href;
}

async function loadDeck(manifestPath) {
  const manifestURL = new URL(manifestPath, location.href).href;
  const response = await fetch(manifestURL, { cache: 'no-cache' });
  if (!response.ok) throw new Error('The presentation manifest could not be loaded.');
  const data = await response.json();
  if (typeof data.id !== 'string' || !data.id || typeof data.title !== 'string' || !data.title
      || !Array.isArray(data.slides) || !data.slides.length) {
    throw new Error('The presentation manifest is incomplete.');
  }
  const ids = new Set();
  const slides = data.slides.map((slide) => {
    if (!slide.id || !slide.title || ids.has(slide.id)) throw new Error('Slide identities must be unique.');
    ids.add(slide.id);
    const result = { ...slide };
    for (const key of ['target', 'render', 'thumbnail', 'scene', 'evidence', 'objects', 'semantic', 'measurement', 'measurement_overlay']) {
      result[key] = artifactURL(slide[key], manifestURL);
    }
    if (!result.render || !result.target) throw new Error('Each slide needs its actual target and render.');
    result.thumbnail ||= result.render;
    return result;
  });
  const downloads = {};
  for (const [key, value] of Object.entries(data.downloads || {})) {
    downloads[key] = artifactURL(value, manifestURL);
  }
  const process = (data.process || []).map((step) => {
    if (!step.title || !step.artifact) throw new Error('Process artifacts need a title and source.');
    return { ...step, artifact: artifactURL(step.artifact, manifestURL) };
  });
  return { ...data, slides, downloads, process, manifestURL, canvas: canvasLayout(data.canvas) };
}

function canvasLayout(value) {
  if (value == null) return null;
  const full = value.full_slide_px;
  const region = value.content_region_px;
  if (!Array.isArray(full) || full.length !== 2 || !Array.isArray(region) || region.length !== 4
      || ![...full, ...region].every((number) => typeof number === 'number' && Number.isFinite(number))
      || full.some((number) => number <= 0) || region[0] < 0 || region[1] < 0
      || region[2] <= 0 || region[3] <= 0 || region[0] + region[2] > full[0] || region[1] + region[3] > full[1]) {
    throw new Error('The generated content region must fit within its slide canvas.');
  }
  return { full_slide_px: full, content_region_px: region };
}

function placeTarget(image, canvas) {
  const [fullWidth, fullHeight] = canvas?.full_slide_px || [16, 9];
  const [left, top, width, height] = canvas?.content_region_px || [0, 0, fullWidth, fullHeight];
  image.style.left = (100 * left / fullWidth) + '%';
  image.style.top = (100 * top / fullHeight) + '%';
  image.style.width = (100 * width / fullWidth) + '%';
  image.style.height = (100 * height / fullHeight) + '%';
}

const reconstructionViewer = createReconstructionViewer({ layer: byId('reconstruction-layer'), panel: byId('reconstruction-panel'), positionLayer: placeTarget });

function deckLabel(deck) { return deck.label || deck.style || deck.title; }
function filename(url) { return decodeURIComponent(new URL(url).pathname.split('/').pop()); }
function extension(url) { return filename(url).split('.').pop().toLowerCase(); }
function isImage(url) { return ['png', 'jpg', 'jpeg', 'webp', 'svg', 'gif'].includes(extension(url)); }

function canAnimate() {
  return document.body.dataset.input !== 'keyboard' && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function focusSection(target, { replace = false } = {}) {
  if (!target.hasAttribute('tabindex')) target.tabIndex = -1;
  target.focus({ preventScroll: true });
  target.scrollIntoView({ block: 'start', behavior: canAnimate() ? 'smooth' : 'instant' });
  const address = new URL(location.href);
  address.hash = target.id;
  history[replace ? 'replaceState' : 'pushState'](null, '', address);
}

function animateViewerChange() {
  if (!canAnimate()) return;
  byId('slide-surface').animate([{ opacity: 0.65 }, { opacity: 1 }], { duration: 180, easing: 'ease-out' });
}

function renderProjects() {
  const grid = byId('project-grid');
  grid.replaceChildren();
  state.decks.forEach((deck, index) => {
    const card = element('button', 'sample-option');
    card.type = 'button';
    card.setAttribute('aria-label', 'Show sample presentation. ' + deck.title);
    card.setAttribute('aria-pressed', 'false');
    card.setAttribute('aria-controls', 'studio');
    const cover = new Image();
    cover.src = deck.slides[0].render;
    cover.alt = '';
    cover.decoding = 'async';
    const caption = element('span', 'sample-option-caption');
    caption.append(element('span', 'sample-option-title', deck.title));
    const metadata = element('span', 'sample-option-meta', deckLabel(deck) + ' · ' + deck.slides.length + ' slides');
    const selected = element('span', 'sample-selected', 'Selected');
    selected.hidden = true;
    caption.append(metadata, selected);
    card.append(cover, caption);
    card.addEventListener('click', () => { if (state.deck !== deck) selectDeck(index); });
    grid.append(card);
  });
}

function download(label, url) {
  const anchor = element('a', '', label);
  anchor.href = url;
  anchor.download = '';
  return anchor;
}

function artifactButton(label, artifact) {
  const button = element('button', '', label);
  button.type = 'button';
  button.addEventListener('click', () => openArtifact({ ...artifact, trigger: button }));
  return button;
}

function updateAddress() {
  const address = new URL(location.href);
  address.searchParams.set('deck', state.deck.id);
  address.searchParams.set('slide', state.deck.slides[state.slideIndex].id);
  if (state.mode === 'rebuilt') address.searchParams.delete('view');
  else address.searchParams.set('view', state.mode);
  history.replaceState(null, '', address);
}

function selectDeck(index, requestedSlideId = null, requestedMode = 'rebuilt') {
  const deck = state.decks[index];
  if (!deck) return;
  const previousId = state.deck?.id;
  state.deck = deck;
  byId('studio').hidden = false;
  [...byId('project-grid').children].forEach((card, i) => {
    card.setAttribute('aria-pressed', String(i === index));
    card.querySelector('.sample-selected').hidden = i !== index;
  });
  byId('viewer-title').textContent = deck.title;
  byId('viewer-sample-meta').textContent = deckLabel(deck) + ' · ' + deck.slides.length + ' slides';
  byId('viewer-dialog').setAttribute('aria-label', deck.title + '. Expanded slide viewer.');
  byId('deck-summary').textContent = deck.summary || '';
  byId('presentation-goal-text').textContent = deck.outline.throughline;
  byId('deck-note').textContent = deck.note || '';
  byId('deck-note').hidden = !deck.note;
  byId('generated-content-note').hidden = !deck.canvas;
  byId('slide-surface').style.aspectRatio = (deck.canvas?.full_slide_px || [16, 9]).join(' / ');
  const downloads = byId('deck-downloads');
  downloads.replaceChildren();
  if (deck.downloads.pptx) downloads.append(download('Download PowerPoint', deck.downloads.pptx));
  const strip = byId('slide-strip');
  strip.replaceChildren();
  deck.slides.forEach((slide, i) => {
    const button = element('button', 'slide-thumb');
    button.type = 'button';
    button.setAttribute('aria-label', 'Slide ' + (i + 1) + '. ' + slide.title);
    const image = new Image();
    image.src = slide.thumbnail;
    image.alt = '';
    image.loading = 'lazy';
    image.decoding = 'async';
    button.append(image, element('span', '', String(i + 1).padStart(2, '0')));
    button.addEventListener('click', () => selectSlide(i));
    strip.append(button);
  });
  setInspectorOpen(false);
  state.mode = ['rebuilt', 'compare', 'target', 'semantic', 'measurements'].includes(requestedMode) ? requestedMode : 'rebuilt';
  const requestedSlide = deck.slides.findIndex((slide) => slide.id === requestedSlideId);
  selectSlide(Math.max(0, requestedSlide), false);
  renderProcess();
  if (previousId && previousId !== deck.id) animateViewerChange();
  announce(deck.title + '. ' + deck.slides.length + ' slides.');
}

function setMode(mode, speak = false) {
  if (!['rebuilt', 'compare', 'target', 'semantic', 'measurements'].includes(mode) || !state.deck) return;
  state.mode = mode;
  reconstructionViewer.clear();
  byId('studio-frame').dataset.mode = mode;
  document.querySelectorAll('.mode-controls button').forEach((button) => {
    button.setAttribute('aria-pressed', String(button.dataset.mode === mode));
  });
  byId('comparison').hidden = mode !== 'compare';
  byId('design-image-open').hidden = mode !== 'target';
  byId('comparison-help').hidden = mode !== 'compare';
  const slide = state.deck.slides[state.slideIndex];
  const preview = byId('slide-preview');
  const source = mode === 'measurements' ? slide.measurement_overlay : ['target', 'semantic'].includes(mode) ? slide.target : slide.render;
  if (preview.src !== source) {
    byId('slide-image-error').hidden = true;
    preview.src = source;
  }
  preview.alt = slide.title + (mode === 'measurements' ? ' OpenCV measurement overlay.' : ['target', 'semantic'].includes(mode) ? ' AI-generated design.' : ' Editable PowerPoint slide.');
  placeTarget(preview, ['target', 'semantic', 'measurements'].includes(mode) ? state.deck.canvas : null);
  if (['semantic', 'measurements'].includes(mode)) reconstructionViewer.show(slide, mode, state.deck.canvas);
  byId('generated-content-note').hidden = !state.deck.canvas || mode === 'rebuilt';
  inspector.setEnabled(mode === 'rebuilt');
  if (mode !== 'rebuilt') setInspectorOpen(false);
  updateObjectStatus();
  updateAddress();
  if (speak) announce(mode === 'rebuilt' ? 'Editable PowerPoint. Select objects to inspect them.' : mode === 'compare' ? 'Compare the design and PowerPoint. Drag the divider or use the range control.' : 'AI-generated design. Select the image to enlarge it.');
}

function selectSlide(index, speak = true) {
  if (!state.deck || index < 0 || index >= state.deck.slides.length) return;
  state.slideIndex = index;
  const slide = state.deck.slides[index];
  byId('slide-title').textContent = slide.title;
  byId('viewer-counter').textContent = String(index + 1).padStart(2, '0') + ' / ' + String(state.deck.slides.length).padStart(2, '0');
  byId('previous-slide').disabled = index === 0;
  byId('next-slide').disabled = index === state.deck.slides.length - 1;
  [...byId('slide-strip').children].forEach((button, i) => button.setAttribute('aria-current', String(i === index)));
  byId('comparison-target').src = slide.target;
  byId('comparison-target').alt = 'AI-generated design for ' + slide.title;
  placeTarget(byId('comparison-target'), state.deck.canvas);
  byId('comparison-render').src = slide.render;
  byId('comparison-render').alt = 'Editable PowerPoint for ' + slide.title;
  setMode(state.mode);
  state.objectLoad = inspector.load(slide.objects);
  if (speak) announce('Slide ' + (index + 1) + ' of ' + state.deck.slides.length + '. ' + slide.title);
}

const WORKFLOW = [
  { id: 'plan', title: 'Plan', description: 'Decide what each slide needs to communicate.', entry: 'Slide outline' },
  { id: 'design', title: 'Design', description: 'Explore layouts using the content and references.', entry: 'Generated design', detail: 'The image-generation prompt includes the slide content, visual references, style guidance and the space available on the page.' },
  { id: 'reconstruct', title: 'Reconstruct', description: 'Build the text, charts and shapes in PowerPoint.', entry: 'Reconstruction' },
  { id: 'review', title: 'Review', description: 'Check each slide and the deck as a whole.', entry: 'Review comparisons' },
];

function workflowFor(deck, configuration) {
  if (!configuration || WORKFLOW.some(({ id }) => !Array.isArray(configuration[id]))) {
    throw new Error('Each sample needs the shared four-stage workflow.');
  }
  const artifacts = new Map(deck.process.map((step) => [step.artifact, step]));
  const seen = new Set();
  const groups = {};
  for (const { id } of WORKFLOW) {
    groups[id] = configuration[id].map((path) => {
      const url = artifactURL(path, deck.manifestURL);
      if (!artifacts.has(url) || seen.has(url)) throw new Error('Workflow evidence must match the retained sample artifacts once.');
      seen.add(url);
      return artifacts.get(url);
    });
  }
  if (seen.size !== artifacts.size) throw new Error('Some sample evidence has no workflow stage.');
  return groups;
}

function lineIcon(path, className) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  if (className) svg.setAttribute('class', className);
  const shape = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  shape.setAttribute('d', path);
  svg.append(shape);
  return svg;
}

function evidencePreview(step, compact = false) {
  const preview = element('span', compact ? 'evidence-thumbnail' : 'workflow-preview');
  preview.setAttribute('aria-hidden', 'true');
  if (isImage(step.artifact)) {
    const image = new Image();
    image.src = step.artifact;
    image.alt = '';
    image.loading = 'lazy';
    image.decoding = 'async';
    image.addEventListener('error', () => preview.replaceChildren(element('span', 'evidence-image-error', 'Preview unavailable')), { once: true });
    preview.append(image);
  } else {
    preview.classList.add('document-preview');
    preview.append(lineIcon('M7 3h7l4 4v14H6V3h1m7 0v5h4M9 12h6m-6 4h6', 'document-icon'));
  }
  return preview;
}

function renderProcess() {
  const container = byId('process-grid');
  const openStages = new Set([...container.querySelectorAll('details[open]')].map((item) => item.dataset.stage));
  container.replaceChildren();
  WORKFLOW.forEach((stage, index) => {
    const steps = state.deck.workflow[stage.id];
    const article = element('article', 'workflow-stage');
    const heading = element('h4');
    heading.append(element('span', 'workflow-number', String(index + 1).padStart(2, '0')), element('span', '', stage.title));
    article.append(heading, element('p', '', stage.description));
    const details = element('details', 'workflow-evidence');
    details.dataset.stage = stage.id;
    details.open = openStages.has(stage.id);
    const summary = element('summary');
    const primary = steps.find((step) => isImage(step.artifact)) || steps[0];
    if (stage.id === 'plan') {
      const preview = element('span', 'workflow-preview plan-miniature');
      preview.setAttribute('aria-hidden', 'true');
      preview.append(element('strong', '', 'Presentation plan'));
      state.deck.outline.slides.filter(item => item.disposition !== 'omitted').forEach((item, index) => {
        const row = element('span', 'plan-miniature-row');
        row.append(element('b', '', String(index + 1).padStart(2, '0')), element('span', '', item.dominant_message));
        preview.append(row);
      });
      summary.append(preview);
    } else if (primary) summary.append(evidencePreview(primary));
    const disclosure = element('span', 'workflow-disclosure', stage.entry);
    disclosure.append(lineIcon('m7 10 5 5 5-5', 'disclosure-chevron'));
    summary.append(disclosure);
    details.append(summary);
    if (stage.detail) details.append(element('p', 'workflow-detail', stage.detail));
    const list = element('ul');
    steps.forEach((step) => {
      const item = element('li');
      const button = artifactButton('', { title: step.title, description: step.description, url: step.artifact });
      const caption = element('span', 'evidence-item-caption');
      caption.append(element('span', 'evidence-item-title', step.title), element('span', 'evidence-item-type', isImage(step.artifact) ? 'Image' : 'Document'));
      button.append(evidencePreview(step, true), caption);
      item.append(button);
      list.append(item);
    });
    details.append(list);
    article.append(details);
    container.append(article);
  });
}

async function fetchJSON(url, signal) {
  const response = await fetch(url, { signal, cache: 'no-cache' });
  if (!response.ok) throw new Error('The evidence file could not be loaded.');
  return response.json();
}

function cropEvidence(container, image, url, box, size, alt) {
  const left = Math.max(0, box[0]);
  const top = Math.max(0, box[1]);
  const width = Math.min(size[0], box[0] + box[2]) - left;
  const height = Math.min(size[1], box[1] + box[3]) - top;
  if (![left, top, width, height, ...size].every(Number.isFinite) || width <= 0 || height <= 0) {
    throw new Error('The walkthrough crop must describe a visible source region.');
  }
  container.style.aspectRatio = String(width / height);
  image.src = url;
  image.alt = alt;
  image.style.width = (100 * size[0] / width) + '%';
  image.style.height = (100 * size[1] / height) + '%';
  image.style.left = (-100 * left / width) + '%';
  image.style.top = (-100 * top / height) + '%';
}

function bindArtifact(id, title, description, url, options = {}) {
  const trigger = byId(id);
  trigger.addEventListener('click', () => openArtifact({ title, description, url, trigger, ...options }));
}

async function loadWalkthrough(configuration) {
  try {
    if (!configuration) throw new Error('No slide walkthrough is configured.');
    const deckIndex = state.decks.findIndex((deck) => deck.id === configuration.showcase_id);
    const deck = state.decks[deckIndex];
    const slide = deck?.slides.find((item) => item.id === configuration.slide_id);
    if (!slide?.objects || !slide.evidence) throw new Error('The walkthrough slide needs actual objects and semantic evidence.');
    const paths = Object.fromEntries(['intent', 'semantic', 'measurement', 'measurement_image'].map((key) => [key, artifactURL(configuration[key], deck.manifestURL)]));
    const [intent, semantic, measurement, rawObjects] = await Promise.all([
      fetchJSON(paths.intent), fetchJSON(paths.semantic), fetchJSON(paths.measurement), fetchJSON(slide.objects),
    ]);
    const objects = validateObjectDocument(rawObjects);
    const mapped = semantic.entities?.find((item) => item.id === configuration.entity_id && item.kind === 'chart');
    const measured = measurement.entities?.find((item) => item.id === configuration.entity_id);
    const native = objects.objects.find((item) => item.name === configuration.entity_id && item.kind === 'chart');
    const briefChart = intent.required_content?.find((item) => item.role === 'native_chart');
    const decision = intent.required_content?.find((item) => item.role === 'decision_band');
    if (!mapped || !measured?.measurement?.visible_bbox?.px || !native || !briefChart) throw new Error('The same chart must be present in the brief, semantic map, measurements and PowerPoint.');
    byId('walkthrough-message').textContent = intent.dominant_message;
    byId('walkthrough-decision').textContent = decision?.message || slide.claim;
    const support = element('span', 'brief-values');
    briefChart.categories.forEach((category, index) => {
      const row = element('span', 'brief-value');
      row.append(element('span', '', category), element('strong', '', Number(briefChart.values[index]).toLocaleString('en-US') + ' h'));
      support.append(row);
    });
    byId('walkthrough-support').replaceChildren(support);
    const target = byId('walkthrough-target');
    target.src = slide.target;
    target.alt = 'Generated composition for ' + slide.title + '. The chart region is outlined.';
    const size = [measurement.source.width_px, measurement.source.height_px];
    target.parentElement.style.aspectRatio = size[0] + ' / ' + size[1];
    const [x, y, width, height] = mapped.bbox_hint;
    const region = byId('walkthrough-chart-region');
    Object.assign(region.style, { left: (100 * x / size[0]) + '%', top: (100 * y / size[1]) + '%', width: (100 * width / size[0]) + '%', height: (100 * height / size[1]) + '%' });
    const crop = [x - 18, y - 30, width + 36, height + 42];
    cropEvidence(byId('walkthrough-semantic-crop'), byId('walkthrough-semantic-image'), slide.evidence, crop, size, 'The Agent maps these columns, labels and values as one native chart.');
    cropEvidence(byId('walkthrough-measurement-crop'), byId('walkthrough-measurement-image'), paths.measurement_image, crop, size, 'OpenCV measurement overlay for the same chart region.');
    byId('walkthrough-semantic-caption').textContent = 'The Agent groups categories and values as one chart.';
    const ink = measured.measurement.visible_bbox.px;
    byId('walkthrough-measurement-caption').textContent = 'OpenCV measures the chart’s position and size.';
    const fullSize = deck.canvas?.full_slide_px || [size[0], size[1]];
    const nativeLeft = Math.min(...native.polygon.map((point) => point[0])) * fullSize[0];
    const nativeTop = Math.min(...native.polygon.map((point) => point[1])) * fullSize[1];
    const nativeWidth = Math.max(...native.polygon.map((point) => point[0])) * fullSize[0] - nativeLeft;
    const nativeHeight = Math.max(...native.polygon.map((point) => point[1])) * fullSize[1] - nativeTop;
    cropEvidence(byId('walkthrough-native-crop'), byId('walkthrough-native-image'), slide.render,
      [nativeLeft - 18, nativeTop - 30, nativeWidth + 36, nativeHeight + 42], fullSize,
      'The reconstructed native chart from the actual PowerPoint render.');
    bindArtifact('walkthrough-brief', 'Slide brief', '', paths.intent, { render: () => renderSlideBrief(intent, slide.planning.inputs) });
    bindArtifact('walkthrough-target-open', 'AI-generated design', 'The generated content image is shown in its final slide position. PowerPoint supplies the shared header and footer.', slide.target, { canvas: deck.canvas });
    bindArtifact('walkthrough-semantic-open', 'Chart interpretation', 'The Agent treats these categories, values and columns as a single editable chart.', slide.evidence, { crop: { box: crop, size } });
    bindArtifact('walkthrough-measurement-open', 'Chart measurements', 'OpenCV records ' + ink[2] + ' × ' + ink[3] + ' pixel bounds around the visible ink in this chart region. The Agent uses this evidence to set object geometry.', paths.measurement_image, { crop: { box: crop, size } });
    state.walkthrough = { deckIndex, slideId: slide.id, objectId: native.id };
    byId('walkthrough').hidden = false;
    byId('walkthrough-loading').hidden = true;
  } catch (error) {
    byId('walkthrough-loading').textContent = 'The slide walkthrough could not be loaded. Its original evidence remains available in the sample viewer.';
    console.error('Slide walkthrough unavailable', error);
  }
}

function renderOutline(data, deck = null) {
  if (!deck || !data.title || !Array.isArray(data.slides)) return null;
  return createPlanView({
    outline: data, slides: deck.slides, signal: state.artifactFetch.signal, announce,
    scrollContainer: byId('artifact-body'),
    loadIntent: (slide, signal) => fetchJSON(slide.planning.intent, signal),
    onShowSlide: (slide) => {
      state.artifactTrigger = byId('studio');
      byId('artifact-dialog').close();
      selectDeck(state.decks.indexOf(deck), slide.id);
      focusSection(byId('studio'), { replace: true });
    },
  });
}

function renderSlideBrief(intent, inputs) {
  const article = element('article', 'brief-document');
  article.append(element('h3', '', intent.dominant_message));
  article.append(createSlideBrief(intent, { inputs, signal: state.artifactFetch.signal }));
  return article;
}

function readableLabel(key) {
  const words = String(key).replace(/[_-]+/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2');
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function structuredFields(value, depth = 0) {
  const list = element('dl', 'document-fields');
  const entries = Array.isArray(value) ? value.map((item, index) => [String(index + 1).padStart(2, '0'), item]) : Object.entries(value);
  for (const [key, item] of entries) {
    const row = element('div', 'document-field');
    if (item !== null && typeof item === 'object') {
      const group = element('details', 'document-group');
      const summary = element('summary');
      const title = Array.isArray(value) ? item.title || item.label || item.name || item.id || key : readableLabel(key);
      const count = Array.isArray(item) ? item.length + ' entries' : Object.keys(item).length + ' fields';
      summary.append(element('span', '', String(title)), element('small', '', count));
      group.append(summary);
      let rendered = false;
      const reveal = () => {
        if (!group.open || rendered) return;
        rendered = true;
        group.append(structuredFields(item, depth + 1));
      };
      group.addEventListener('toggle', reveal);
      if (!depth && ['observations', 'decisions', 'notes', 'findings'].includes(key)) { group.open = true; reveal(); }
      const branch = element('dd', 'document-branch');
      branch.append(group);
      row.append(element('dt', 'sr-only', String(title)), branch);
    } else {
      const text = item === null ? 'Not recorded' : typeof item === 'boolean' ? item ? 'Yes' : 'No' : String(item);
      row.append(element('dt', '', readableLabel(key)), element('dd', '', text));
    }
    list.append(row);
  }
  return list;
}

function renderSourceDocument(data, title, raw) {
  const article = element('article', 'source-document');
  article.tabIndex = 0;
  article.setAttribute('aria-label', title);
  article.append(element('p', 'eyebrow', 'Behind the sample'), element('h3', '', title));
  if (data && typeof data === 'object') article.append(structuredFields(data));
  else article.append(element('p', 'document-text', raw));
  return article;
}

function unavailableArtifact(message) {
  const content = element('div', 'artifact-unavailable');
  content.append(element('p', '', message), element('p', '', 'Close this preview and choose another sample artifact.'));
  return content;
}

function animateArtifact(opening) {
  state.artifactMotion?.cancel();
  if (!canAnimate()) return null;
  const dialog = byId('artifact-dialog');
  const source = state.artifactTrigger?.getBoundingClientRect();
  const bounds = dialog.getBoundingClientRect();
  if (source) dialog.style.transformOrigin = (source.left + source.width / 2 - bounds.left) + 'px ' + (source.top + source.height / 2 - bounds.top) + 'px';
  const frames = [{ opacity: 0, transform: 'scale(.97)' }, { opacity: 1, transform: 'scale(1)' }];
  state.artifactMotion = dialog.animate(opening ? frames : [...frames].reverse(), {
    duration: opening ? 180 : 120, easing: 'cubic-bezier(.2,.7,.2,1)',
  });
  return state.artifactMotion;
}

function closeArtifact() {
  const dialog = byId('artifact-dialog');
  if (!dialog.open) return;
  const motion = animateArtifact(false);
  if (!motion) { dialog.close(); return; }
  motion.finished.then(() => { if (state.artifactMotion === motion) dialog.close(); }).catch(() => {});
}

async function openArtifact({ title, description = '', url, trigger = document.activeElement, crop = null, render = null, canvas = null }) {
  if (!url) return;
  const dialog = byId('artifact-dialog');
  const opening = !dialog.open;
  state.artifactMotion?.cancel();
  if (opening) state.artifactTrigger = trigger;
  const request = ++state.artifactRequest;
  state.artifactFetch?.abort();
  state.artifactFetch = new AbortController();
  byId('artifact-title').textContent = title;
  byId('artifact-type').textContent = isImage(url) ? 'Image' : 'Document';
  byId('artifact-description').textContent = description;
  byId('artifact-description').hidden = !description;
  const body = byId('artifact-body');
  body.replaceChildren(element('p', 'artifact-loading', 'Loading the source artifact…'));
  if (!dialog.open) dialog.showModal();
  if (render) {
    body.replaceChildren(render());
    if (opening) animateArtifact(true);
    return;
  }
  if (opening) animateArtifact(true);
  const format = extension(url);
  if (isImage(url)) {
    const image = new Image();
    image.alt = description || title;
    image.addEventListener('load', () => {
      if (request !== state.artifactRequest || !dialog.open) return;
      if (crop) {
        const region = element('div', 'artifact-crop evidence-crop');
        cropEvidence(region, image, url, crop.box, crop.size, description || title);
        region.append(image);
        body.replaceChildren(region);
      } else if (canvas) {
        const frame = element('div', 'artifact-slide-frame');
        frame.style.aspectRatio = canvas.full_slide_px.join(' / ');
        placeTarget(image, canvas);
        frame.append(image);
        body.replaceChildren(frame);
      } else body.replaceChildren(image);
    }, { once: true });
    image.addEventListener('error', () => {
      if (request === state.artifactRequest && dialog.open) body.replaceChildren(unavailableArtifact('This image could not be loaded.'));
    }, { once: true });
    image.src = url;
  } else if (format === 'pdf') {
    const object = element('object');
    object.data = url;
    object.type = 'application/pdf';
    object.setAttribute('aria-label', title);
    object.append(unavailableArtifact('This browser cannot display the PDF inline.'));
    body.replaceChildren(object);
  } else if (['json', 'txt', 'md'].includes(format)) {
    try {
      const response = await fetch(url, { signal: state.artifactFetch.signal });
      if (!response.ok) throw new Error('The source file could not be loaded.');
      const raw = await response.text();
      if (request !== state.artifactRequest || !dialog.open) return;
      const data = format === 'json' ? JSON.parse(raw) : null;
      const deck = state.decks.find((sample) => sample.outlineURL === url);
      const outline = data && renderOutline(data, deck);
      if (outline) body.replaceChildren(outline);
      else {
        body.replaceChildren(renderSourceDocument(data, title, raw));
      }
    } catch (error) {
      if (request !== state.artifactRequest || error.name === 'AbortError' || !dialog.open) return;
      body.replaceChildren(unavailableArtifact('The source preview could not be loaded.'));
    }
  } else body.replaceChildren(unavailableArtifact('This file does not have an inline preview.'));
}

function wireDialog(dialog, closeButton, closed, close = () => dialog.close()) {
  closeButton?.addEventListener('click', close);
  dialog.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) close();
  });
  dialog.addEventListener('close', closed);
}

wireDialog(byId('artifact-dialog'), byId('artifact-close'), () => {
  ++state.artifactRequest;
  state.artifactFetch?.abort();
  state.artifactMotion?.cancel();
  byId('artifact-body').replaceChildren();
  if (state.artifactTrigger?.isConnected) state.artifactTrigger.focus({ preventScroll: true });
}, closeArtifact);
byId('artifact-dialog').addEventListener('cancel', (event) => {
  event.preventDefault();
  closeArtifact();
});

const viewerHome = document.createComment('Inline presentation viewer');
function updateExpandedControl(expanded) {
  const button = byId('expand-viewer');
  button.setAttribute('aria-expanded', String(expanded));
  button.setAttribute('aria-label', expanded ? 'Close expanded viewer' : 'Expand presentation viewer');
  button.title = expanded ? 'Close expanded viewer' : 'Expand viewer';
  button.querySelector('path').setAttribute('d', expanded
    ? 'm5 5 10 10M5 15 15 5'
    : 'M7 3H3v4m10-4h4v4M3 13v4h4m10-4v4h-4');
}
function restoreInlineViewer() {
  if (viewerHome.isConnected) viewerHome.replaceWith(byId('studio-frame'));
  updateExpandedControl(false);
  if (state.viewerScroll) window.scrollTo({ ...state.viewerScroll, behavior: 'instant' });
  state.viewerScroll = null;
  byId('expand-viewer').focus({ preventScroll: true });
}
wireDialog(byId('viewer-dialog'), null, restoreInlineViewer);
byId('viewer-dialog').addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  event.preventDefault();
  event.stopPropagation();
  byId('viewer-dialog').close();
}, { capture: true });
byId('expand-viewer').addEventListener('click', () => {
  const dialog = byId('viewer-dialog');
  if (dialog.open) { dialog.close(); return; }
  const frame = byId('studio-frame');
  state.viewerScroll = { top: window.scrollY, left: window.scrollX };
  frame.before(viewerHome);
  dialog.append(frame);
  updateExpandedControl(true);
  try {
    dialog.showModal();
    byId('expand-viewer').focus({ preventScroll: true });
  } catch {
    restoreInlineViewer();
    announce('The expanded view could not be opened. The inline presentation remains available.');
  }
});

document.querySelectorAll('a[href^="#"]').forEach((anchor) => anchor.addEventListener('click', (event) => {
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const target = document.getElementById(anchor.getAttribute('href').slice(1));
  if (!target) return;
  event.preventDefault();
  focusSection(target);
}));
function setConsoleInteraction(active) {
  const frame = byId('console-frame');
  byId('console-enter').hidden = active;
  byId('console-controls').hidden = !active;
  frame.inert = !active;
  frame.tabIndex = active ? 0 : -1;
  byId('console-demo').dataset.active = String(active);
  (active ? frame : byId('console-enter')).focus({ preventScroll: true });
}
byId('console-enter').addEventListener('click', () => setConsoleInteraction(true));
byId('console-done').addEventListener('click', () => setConsoleInteraction(false));

byId('copy-install').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(byId('install-command').textContent);
    byId('copy-status').textContent = 'Installation command copied.';
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(byId('install-command'));
    selection.removeAllRanges();
    selection.addRange(range);
    byId('copy-status').textContent = 'Command selected. Use your keyboard to copy it.';
  }
});
document.addEventListener('pointerdown', () => { document.body.dataset.input = 'pointer'; }, { passive: true });
document.addEventListener('keydown', () => { document.body.dataset.input = 'keyboard'; });
document.querySelectorAll('.mode-controls button').forEach((button) => button.addEventListener('click', () => setMode(button.dataset.mode, true)));
byId('object-toggle').addEventListener('click', () => setInspectorOpen(!state.inspectorOpen));
byId('presentation-goal').addEventListener('click', () => {
  const deck = state.deck;
  if (deck) openArtifact({ title: 'Presentation plan', url: deck.outlineURL, trigger: byId('presentation-goal'), render: () => renderOutline(deck.outline, deck) });
});
byId('design-image-open').addEventListener('click', () => {
  const slide = state.deck?.slides[state.slideIndex];
  if (slide) openArtifact({ title: 'AI-generated design', description: slide.title, url: slide.target, trigger: byId('design-image-open'), canvas: state.deck.canvas });
});
byId('walkthrough-native-open').addEventListener('click', async () => {
  const example = state.walkthrough;
  if (!example) return;
  selectDeck(example.deckIndex, example.slideId);
  focusSection(byId('studio'), { replace: true });
  await state.objectLoad;
  if (state.deck?.id !== state.decks[example.deckIndex].id || state.deck.slides[state.slideIndex]?.id !== example.slideId || state.mode !== 'rebuilt') return;
  inspector.select(example.objectId, { focusCanvas: true });
});
byId('previous-slide').addEventListener('click', () => selectSlide(state.slideIndex - 1));
byId('next-slide').addEventListener('click', () => selectSlide(state.slideIndex + 1));
byId('slide-preview').addEventListener('error', () => { byId('slide-image-error').hidden = false; });
byId('slide-preview').addEventListener('load', () => { byId('slide-image-error').hidden = true; });
byId('reveal').addEventListener('input', (event) => {
  const value = Number(event.currentTarget.value);
  byId('comparison-render').style.clipPath = 'inset(0 ' + (100 - value) + '% 0 0)';
  byId('comparison-divider').style.left = value + '%';
  event.currentTarget.setAttribute('aria-valuetext', value + ' percent editable PowerPoint, ' + (100 - value) + ' percent AI-generated design');
});
byId('reveal').setAttribute('aria-valuetext', '50 percent editable PowerPoint, 50 percent AI-generated design');

const initialFragment = location.hash;
const initialNavigationGuard = new AbortController();
let initialNavigationInterrupted = false;
const interruptInitialNavigation = () => { initialNavigationInterrupted = true; };
for (const type of ['pointerdown', 'wheel', 'touchstart', 'keydown', 'click']) {
  document.addEventListener(type, interruptInitialNavigation, { capture: true, passive: true, signal: initialNavigationGuard.signal });
}
for (const type of ['hashchange', 'popstate']) {
  window.addEventListener(type, interruptInitialNavigation, { signal: initialNavigationGuard.signal });
}

async function restoreInitialFragment() {
  await new Promise((resolve) => requestAnimationFrame(resolve));
  if (!initialNavigationInterrupted && initialFragment && location.hash === initialFragment) {
    const identity = initialFragment === '#work' ? 'studio' : initialFragment.slice(1);
    const target = document.getElementById(identity);
    if (target?.getClientRects().length) target.scrollIntoView({ block: 'start', behavior: 'instant' });
  }
  initialNavigationGuard.abort();
}

async function start() {
  try {
    const response = await fetch('./showcases.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error('The showcase index could not be loaded.');
    const index = await response.json();
    if (!Array.isArray(index.showcases) || !index.showcases.length) throw new Error('No presentations are listed.');
    const results = await Promise.allSettled(index.showcases.map(async (path) => {
      const deck = await loadDeck(path);
      deck.summary = index.presentation_summaries?.[deck.id] || deck.summary;
      const labels = new Map(Object.entries(index.artifact_labels?.[deck.id] || {}).map(([artifact, label]) => [artifactURL(artifact, deck.manifestURL), label]));
      deck.process = deck.process.map((step) => ({ ...step, title: labels.get(step.artifact) || step.title }));
      deck.workflow = workflowFor(deck, index.workflow?.[deck.id]);
      deck.outlineURL = artifactURL(index.brief_sources?.[deck.id], deck.manifestURL);
      if (!deck.outlineURL) throw new Error('Each sample needs its original presentation outline.');
      deck.outline = await fetchJSON(deck.outlineURL);
      const planning = index.planning_inputs?.[deck.id];
      if (!planning || Object.keys(planning).length !== deck.slides.length) throw new Error('Each sample needs its full per-slide planning inputs.');
      deck.slides.forEach((slide) => {
        const source = planning[slide.id];
        if (!source?.intent || !Array.isArray(source.inputs) || !source.inputs.length) throw new Error('A full slide input is missing.');
        slide.planning = {
          intent: artifactURL(source.intent, deck.manifestURL),
          inputs: source.inputs.map((input) => {
            if (!input.label || !input.path) throw new Error('Recorded image-generation inputs need a label and source.');
            return { label: input.label, url: artifactURL(input.path, deck.manifestURL) };
          }),
        };
      });
      if (typeof deck.outline.throughline !== 'string' || !deck.outline.throughline.trim()
          || !Array.isArray(deck.outline.slides)
          || deck.slides.some((slide) => !deck.outline.slides.some((entry) => entry.slide_id === slide.id && entry.dominant_message))) {
        throw new Error('The presentation outline must describe the actual sample slides.');
      }
      return deck;
    }));
    state.decks = results.filter((result) => result.status === 'fulfilled').map((result) => result.value);
    if (!state.decks.length) throw new Error('No complete presentation manifest could be loaded.');
    if (new Set(state.decks.map((deck) => deck.id)).size !== state.decks.length) throw new Error('Presentation identities must be unique.');
    renderProjects();
    const requested = new URLSearchParams(location.search);
    const deck = state.decks.findIndex((item) => item.id === requested.get('deck'));
    selectDeck(deck >= 0 ? deck : Math.max(0, state.decks.findIndex(item => item.id === 'personal-thinking-system')), requested.get('slide'), requested.get('view'));
    const walkthroughReady = loadWalkthrough(index.walkthrough);
    byId('load-state').hidden = true;
    if (results.some((result) => result.status === 'rejected')) {
      byId('load-state').textContent = 'One presentation is temporarily unavailable. The available example is shown below.';
      byId('load-state').hidden = false;
    }
    await walkthroughReady;
  } catch (error) {
    byId('load-state').textContent = 'The presentations could not be loaded. Serve the repository over HTTP with its examples directory in place.';
    console.error('Showcase unavailable', error);
  } finally {
    await restoreInitialFragment();
  }
}
start();
