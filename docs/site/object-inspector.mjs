const SVG = 'http://www.w3.org/2000/svg';
const KIND_LABELS = { text: 'Text', shape: 'Shape', image: 'Image', chart: 'Chart', table: 'Table', connector: 'Connector' };

export function validateObjectDocument(value) {
  if (!value || value.schema_version !== 1 || !Array.isArray(value.objects)
      || !Number.isFinite(value.size?.width) || !Number.isFinite(value.size?.height)
      || value.size.width <= 0 || value.size.height <= 0) {
    throw new Error('The object preview has invalid slide dimensions.');
  }
  const ids = new Set();
  for (const item of value.objects) {
    if (!item.id || typeof item.id !== 'string' || ids.has(item.id) || !KIND_LABELS[item.kind]
        || typeof item.label !== 'string' || !Array.isArray(item.polygon) || item.polygon.length !== 4
        || !item.polygon.every(point => Array.isArray(point) && point.length === 2 && point.every(Number.isFinite))) {
      throw new Error('The object preview contains invalid selection geometry.');
    }
    if (item.line && (!Array.isArray(item.line) || item.line.length !== 2
        || !item.line.every(point => Array.isArray(point) && point.length === 2 && point.every(Number.isFinite)))) {
      throw new Error('The object preview contains an invalid connector.');
    }
    ids.add(item.id);
  }
  return value;
}

/** One focus stop for the canvas. Arrow keys navigate native stacking order. */
export function nextObjectIndex(current, key, length) {
  if (!length) return null;
  if (key === 'Home') return 0;
  if (key === 'End') return length - 1;
  if (key === 'ArrowRight' || key === 'ArrowDown') return current < 0 ? 0 : (current + 1) % length;
  if (key === 'ArrowLeft' || key === 'ArrowUp') return current < 0 ? length - 1 : (current - 1 + length) % length;
  return null;
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function svgElement(tag, attributes = {}) {
  const node = document.createElementNS(SVG, tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, String(value));
  return node;
}

function appendTable(parent, rows, captionText) {
  if (!rows?.length) return;
  const table = element('table', 'oi-table');
  if (captionText) table.append(element('caption', '', captionText));
  const body = element('tbody');
  for (const row of rows) {
    const tr = element('tr');
    row.forEach((value, index) => tr.append(element(index ? 'td' : 'th', '', value ?? '')));
    body.append(tr);
  }
  table.append(body);
  const scroll = element('div', 'oi-table-scroll');
  scroll.append(table);
  parent.append(scroll);
}

export function createObjectInspector({ surface, panel, announce = () => {},
  onSelectionChange = () => {}, onStateChange = () => {} }) {
  if (!surface || !panel) throw new Error('The object inspector needs a slide surface and panel.');
  let current = null;
  let enabled = true;
  let selected = -1;
  let generation = 0;
  let pending = null;
  let destroyed = false;
  let targets = [];
  let layerButtons = [];
  const canvas = svgElement('svg', { class: 'object-inspector-layer', viewBox: '0 0 1000 562.5',
    role: 'listbox', tabindex: '0', 'aria-label': 'PowerPoint objects. Use arrow keys to select. Escape clears selection.' });
  const targetGroup = svgElement('g');
  const selectedShape = svgElement('polygon', { class: 'oi-selection', 'aria-hidden': 'true' });
  selectedShape.style.display = 'none';
  canvas.append(targetGroup, selectedShape);
  surface.append(canvas);
  panel.classList.add('object-inspector-panel');
  const panelHeading = element('div', 'oi-panel-heading');
  panelHeading.append(element('h3', '', 'Object inspector'), element('span', 'oi-readonly', 'Read-only'));
  const selectionInfo = element('div', 'oi-info');
  const layers = element('details', 'oi-layers');
  const layerSummary = element('summary', '', 'Layers');
  const layerList = element('div', 'oi-layer-list');
  layers.append(layerSummary, layerList);
  panel.append(panelHeading, selectionInfo, layers);

  function status(message, state = 'ready') {
    selectionInfo.replaceChildren(element('p', 'oi-empty', message));
    onStateChange({ status: state, objectCount: current?.objects.length || 0 });
  }

  function showDetails(item) {
    selectionInfo.replaceChildren(element('span', 'oi-kind', KIND_LABELS[item.kind]), element('h4', 'oi-object-title', item.label));
    if (item.kind === 'text') {
      const families = [...new Set((item.typography || []).map(style => style.family).filter(Boolean))];
      const sizes = [...new Set((item.typography || []).map(style => style.size_pt).filter(Number.isFinite))];
      const meta = [...families, ...sizes.map(size => `${size} pt`)];
      if (meta.length) selectionInfo.append(element('p', 'oi-meta', meta.join(' · ')));
      selectionInfo.append(element('p', 'oi-text-content', item.text || ''));
    } else if (item.kind === 'chart') {
      for (const series of item.chart?.series || []) {
        appendTable(selectionInfo, (series.categories || []).map((category, index) => [category, series.values?.[index]]), series.name);
      }
      selectionInfo.append(element('p', 'oi-meta', 'Native PowerPoint chart data'));
    } else if (item.kind === 'table') {
      appendTable(selectionInfo, item.rows, 'PowerPoint table');
    } else if (item.kind === 'image') {
      selectionInfo.append(element('p', 'oi-meta', 'A preserved image region. Text within this artwork belongs to the image.'));
    } else if (item.kind === 'connector') {
      const arrow = Object.values(item.arrows || {}).some(end => end.type && end.type !== 'none');
      selectionInfo.append(element('p', 'oi-meta', arrow ? 'Native connector with an arrowhead' : 'Native connector'));
    } else {
      selectionInfo.append(element('p', 'oi-meta', 'Native PowerPoint shape'));
    }
  }

  function choose(index, { focusCanvas = false, speak = true } = {}) {
    if (!enabled || !current || index < 0 || index >= current.objects.length) return;
    selected = index;
    const item = current.objects[index];
    targets.forEach((target, i) => target.setAttribute('aria-selected', String(i === index)));
    layerButtons.forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
    const height = 1000 * current.size.height / current.size.width;
    selectedShape.setAttribute('points', item.polygon.map(([x, y]) => `${x * 1000},${y * height}`).join(' '));
    selectedShape.style.display = '';
    canvas.setAttribute('aria-activedescendant', targets[index].id);
    showDetails(item);
    onSelectionChange(item);
    if (speak) announce(`${KIND_LABELS[item.kind]} selected. ${item.label}. Read-only.`);
    if (focusCanvas) canvas.focus({ preventScroll: true });
  }

  function clearSelection({ speak = false } = {}) {
    selected = -1;
    selectedShape.style.display = 'none';
    canvas.removeAttribute('aria-activedescendant');
    targets.forEach(target => target.setAttribute('aria-selected', 'false'));
    layerButtons.forEach(button => button.setAttribute('aria-pressed', 'false'));
    if (current) status('Select an object on the slide, or browse its layers. Use arrow keys to move between objects.');
    onSelectionChange(null);
    if (speak) announce('Selection cleared.');
  }

  function reset() {
    current = null;
    selected = -1;
    targets = [];
    layerButtons = [];
    targetGroup.replaceChildren();
    layerList.replaceChildren();
    selectedShape.style.display = 'none';
    canvas.removeAttribute('aria-activedescendant');
    layerSummary.textContent = 'Layers';
    layers.hidden = true;
    onSelectionChange(null);
  }

  function showDocument(data) {
    current = validateObjectDocument(data);
    const height = 1000 * current.size.height / current.size.width;
    canvas.setAttribute('viewBox', `0 0 1000 ${height}`);
    current.objects.forEach((item, index) => {
      const group = svgElement('g', { role: 'option', 'aria-label': `${KIND_LABELS[item.kind]}. ${item.label}`,
        'aria-selected': 'false', id: `oi-${generation}-${index}`, class: `oi-target oi-${item.kind}`, 'data-native-kind': item.kind });
      const attributes = { class: 'oi-hit-area', points: item.polygon.map(([x, y]) => `${x * 1000},${y * height}`).join(' ') };
      const region = item.line
        ? svgElement('line', { class: 'oi-hit-line', x1: item.line[0][0] * 1000, y1: item.line[0][1] * height,
          x2: item.line[1][0] * 1000, y2: item.line[1][1] * height })
        : svgElement('polygon', attributes);
      group.append(region, svgElement('title'));
      group.lastChild.textContent = item.label;
      group.addEventListener('click', event => { event.stopPropagation(); choose(index, { focusCanvas: true }); });
      targetGroup.append(group);
      targets.push(group);
      const button = element('button', 'oi-layer');
      button.type = 'button';
      button.setAttribute('aria-pressed', 'false');
      button.append(element('span', 'oi-layer-kind', KIND_LABELS[item.kind]), element('span', 'oi-layer-name', item.label));
      button.addEventListener('click', () => choose(index));
      layerButtons.push(button);
      layerList.append(button);
    });
    layerSummary.textContent = `Layers · ${current.objects.length}`;
    layers.hidden = !current.objects.length;
    clearSelection();
  }

  const keydown = event => {
    if (!enabled || !current || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      clearSelection({ speak: true });
      return;
    }
    const index = nextObjectIndex(selected, event.key, current.objects.length);
    if (index !== null) {
      event.preventDefault();
      event.stopPropagation();
      choose(index);
    }
  };
  canvas.addEventListener('keydown', keydown);
  canvas.addEventListener('click', () => clearSelection({ speak: true }));
  status('Choose a slide to inspect its objects.');

  return {
    select(id, options = {}) {
      const index = current?.objects.findIndex(item => item.id === id) ?? -1;
      if (!enabled || index < 0) return false;
      choose(index, options);
      return true;
    },
    async load(url) {
      if (destroyed) return;
      const request = ++generation;
      pending?.abort();
      pending = new AbortController();
      reset();
      if (!url) { status('Object inspection is unavailable for this slide.', 'unavailable'); return; }
      status('Loading PowerPoint objects…', 'loading');
      try {
        const response = await fetch(url, { signal: pending.signal, cache: 'no-cache' });
        if (!response.ok) throw new Error('The object preview could not be loaded.');
        const data = await response.json();
        if (request !== generation || destroyed) return;
        showDocument(data);
      } catch (error) {
        if (request !== generation || destroyed || error.name === 'AbortError') return;
        reset();
        status('Object inspection is unavailable. You can still browse and download the presentation.', 'error');
      }
    },
    setEnabled(value) {
      enabled = Boolean(value);
      canvas.hidden = !enabled;
      canvas.style.display = enabled ? '' : 'none';
      canvas.setAttribute('tabindex', enabled ? '0' : '-1');
      if (!enabled) clearSelection();
    },
    clear() {
      ++generation;
      pending?.abort();
      reset();
      status('Choose a slide to inspect its objects.', 'empty');
    },
    destroy() {
      destroyed = true;
      ++generation;
      pending?.abort();
      canvas.remove();
      panel.replaceChildren();
    },
  };
}
