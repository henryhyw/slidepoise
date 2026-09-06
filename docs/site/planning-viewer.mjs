/* Readable views over retained planning inputs. The source files stay unchanged. */
function node(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
}
function label(value) { return String(value).replace(/[_-]+/g, ' ').replace(/^./, (letter) => letter.toUpperCase()); }
function list(values, className = '') {
  const result = node('ul', className);
  values.forEach((value) => result.append(node('li', '', String(value))));
  return result;
}
function section(title, content) {
  const result = node('section', 'plan-section');
  result.append(node('h4', '', title), content);
  return result;
}
function disclosure(title, content) {
  const result = node('details', 'plan-disclosure');
  result.append(node('summary', '', title), content);
  return result;
}
function table(columns, rows, title) {
  const wrapper = node('div', 'plan-table-scroll');
  wrapper.tabIndex = 0;
  wrapper.setAttribute('aria-label', title || 'Slide data table');
  const result = node('table', 'plan-table');
  const head = node('thead');
  const heading = node('tr');
  columns.forEach((text) => { const cell = node('th', '', String(text)); cell.scope = 'col'; heading.append(cell); });
  head.append(heading);
  const body = node('tbody');
  rows.forEach((row) => { const line = node('tr'); row.forEach((text) => line.append(node('td', '', String(text)))); body.append(line); });
  result.append(head, body);
  wrapper.append(result);
  return wrapper;
}
function fields(value) {
  if (Array.isArray(value)) {
    if (value.every((item) => item === null || typeof item !== 'object')) return list(value);
    if (value.length && value.every((item) => item?.value !== undefined && item.label && item.calculation && Object.keys(item).every((key) => ['value', 'label', 'calculation'].includes(key)))) {
      return table(['Metric', 'Value', 'Calculation'], value.map((item) => [item.label, item.value, item.calculation]), 'Metric calculations');
    }
    if (value.length && value.every((item) => item?.number && item.heading && item.detail)) {
      const argumentsList = node('ol', 'plan-arguments');
      value.forEach((item) => {
        const row = node('li');
        const content = node('div');
        content.append(node('strong', '', item.heading), node('p', '', item.detail));
        const remaining = Object.fromEntries(Object.entries(item).filter(([key]) => !['number', 'heading', 'detail'].includes(key)));
        if (Object.keys(remaining).length) content.append(fields(remaining));
        row.append(node('span', 'plan-argument-number', item.number), content);
        argumentsList.append(row);
      });
      return argumentsList;
    }
    if (value.length && value.every((item) => item?.title && item.evidence && Object.keys(item).every((key) => ['title', 'evidence'].includes(key)))) {
      return table(['Milestone', 'Evidence'], value.map((item) => [item.title, item.evidence]), 'Milestone evidence');
    }
    const items = node('div', 'plan-blocks');
    value.forEach((item) => items.append(fields(item)));
    return items;
  }
  if (value && typeof value === 'object') {
    if ((value.source && value.target) || (value.from && value.to)) return connection(value);
    const headingKey = value.label ? 'label' : 'heading';
    const copyKey = ['text', 'message', 'body', 'detail'].find((key) => value[key]);
    const heading = value[headingKey];
    const copy = value[copyKey];
    if (heading && copy) {
      const result = node('div', 'plan-named-copy');
      result.append(node('strong', '', heading), node('p', '', copy));
      const remaining = Object.fromEntries(Object.entries(value).filter(([key]) => key !== headingKey && key !== copyKey));
      if (Object.keys(remaining).length) result.append(fields(remaining));
      return result;
    }
    const result = node('dl', 'plan-fields');
    for (const [key, item] of Object.entries(value)) {
      const row = node('div');
      const detail = node('dd');
      detail.append(item && typeof item === 'object' ? fields(item) : node('span', '', String(item ?? '')));
      row.append(node('dt', '', label(key)), detail);
      result.append(row);
    }
    return result;
  }
  return node('p', '', String(value ?? ''));
}
function sequence(values, directed = true) {
  const result = node('p', 'plan-connection-line');
  values.forEach((value, index) => {
    if (index) result.append(node('span', 'plan-connection-arrow', directed ? '→' : '·'));
    result.append(node('span', '', String(value)));
  });
  return result;
}
function connection(value) {
  const result = node('div', 'plan-connection');
  result.append(sequence([value.source || value.from, value.target || value.to]));
  if (value.factors?.length) result.append(node('p', 'plan-connection-note', value.factors.join(' × ')));
  if (value.condition) result.append(node('p', 'plan-connection-note', 'Required condition · ' + value.condition));
  if (value.label) result.append(node('p', 'plan-connection-note', value.label));
  const remaining = Object.fromEntries(Object.entries(value).filter(([key]) => !['type', 'source', 'target', 'from', 'to', 'factors', 'condition', 'label'].includes(key)));
  if (Object.keys(remaining).length) result.append(fields(remaining));
  return result;
}
function relationships(values) {
  const result = node('div', 'plan-connections');
  values.forEach((value) => {
    if (value.source && value.target) { result.append(connection(value)); return; }
    if (value.members) {
      const item = node('div', 'plan-connection');
      item.append(sequence(value.members, ['directed_sequence', 'dependency'].includes(value.type)));
      if (value.dimensions?.length) item.append(node('p', 'plan-connection-note', 'Compare ' + value.dimensions.join(', ')));
      const remaining = Object.fromEntries(Object.entries(value).filter(([key]) => !['type', 'members', 'dimensions'].includes(key)));
      if (Object.keys(remaining).length) item.append(fields(remaining));
      result.append(item);
      return;
    }
    result.append(fields(Object.fromEntries(Object.entries(value).filter(([key]) => key !== 'type'))));
  });
  return result;
}
function contentBlock(item) {
  if (typeof item === 'string') return node('p', 'plan-copy', item);
  const block = node('section', 'plan-content-block');
  const title = item.heading || item.label;
  if (title) block.append(node('h5', '', title));
  if (item.text) block.append(node('p', item.role === 'formula' ? 'plan-formula' : 'plan-copy', item.text));
  if (item.message) block.append(node('p', 'plan-decision', item.message));
  if (item.qualification) block.append(node('p', 'plan-qualification', item.qualification));
  if (item.equation) block.append(node('p', 'plan-formula', item.equation));
  if (item.term_labels) block.append(node('p', 'plan-qualification', item.term_labels.join(' · ')));
  if (item.valuation) block.append(node('p', 'plan-copy', item.valuation));
  if (item.stages) block.append(sequence(item.stages));
  if (Array.isArray(item.columns) && Array.isArray(item.rows)) block.append(table(item.columns, item.rows, title));
  if (Array.isArray(item.categories) && Array.isArray(item.values)) {
    block.append(table(['Category', item.qualification || 'Value'], item.categories.map((category, index) => [category, item.values[index]]), title));
  }
  if (Array.isArray(item.items)) block.append(fields(item.items));
  const rendered = new Set(['role', 'heading', 'label', 'text', 'message', 'qualification', 'columns', 'rows', 'categories', 'values', 'items', 'equation', 'term_labels', 'valuation', 'stages']);
  const remainder = Object.fromEntries(Object.entries(item).filter(([key]) => !rendered.has(key)));
  if (Object.keys(remainder).length) block.append(fields(remainder));
  return block;
}
function appendSources(parent, inputs, signal) {
  for (const input of inputs) {
    const detail = disclosure(input.label, node('div', 'generation-input-body'));
    const body = detail.lastElementChild;
    let loaded = false;
    detail.addEventListener('toggle', async () => {
      if (!detail.open || loaded) return;
      loaded = true;
      body.replaceChildren(node('p', 'plan-loading', 'Loading the recorded input…'));
      try {
        const response = await fetch(input.url, { signal });
        if (!response.ok) throw new Error('Input unavailable');
        const raw = await response.text();
        if (signal?.aborted || !detail.isConnected) return;
        const data = input.url.endsWith('.json') ? JSON.parse(raw) : null;
        const prompt = data ? data.prompt : raw;
        if (typeof prompt !== 'string' || !prompt.trim()) throw new Error('No recorded prompt');
        const source = node('pre', 'generation-input', prompt);
        source.tabIndex = 0;
        source.setAttribute('aria-label', input.label);
        body.replaceChildren(source);
      } catch (error) {
        if (signal?.aborted) return;
        loaded = false;
        body.replaceChildren(node('p', 'plan-error', 'This recorded input could not be loaded. Close and reopen this section to retry.'));
      }
    });
    parent.append(detail);
  }
}

export function createSlideBrief(intent, { planningNotes = [], inputs = [], signal } = {}) {
  if (!intent?.dominant_message || !Array.isArray(intent.required_content) || !intent.required_content.length) {
    throw new Error('The full slide content is unavailable.');
  }
  const article = node('article', 'slide-plan');
  const content = node('div', 'plan-blocks');
  intent.required_content.forEach((item) => content.append(contentBlock(item)));
  article.append(section('Slide content', content));
  if (intent.semantic_relationships?.length) article.append(section('How the information connects', relationships(intent.semantic_relationships)));
  const assumptions = [...new Set([...(intent.evidence || []), ...(intent.assumptions || [])])];
  if (assumptions.length) article.append(section('Evidence and assumptions', list(assumptions)));
  if (planningNotes.length) article.append(disclosure('Supporting planning notes', list(planningNotes)));
  const design = node('div', 'plan-design');
  const groups = [
    ['Visual hierarchy', intent.hierarchy],
    ['Visual requirements', [...new Set([...(intent.visual_obligations || []), ...(intent.explicit_user_visual_requirements || [])])]],
    ['Avoid', intent.avoid],
  ];
  for (const [title, values] of groups) if (values?.length) design.append(section(title, list(values)));
  if (design.childElementCount) article.append(disclosure('Design instructions', design));
  if (inputs.length) appendSources(article, inputs, signal);
  return article;
}

export function createPlanView({ outline, slides, loadIntent, onShowSlide, announce = () => {}, signal, scrollContainer }) {
  const article = node('article', 'presentation-plan');
  article.append(node('h3', '', outline.title), node('p', 'plan-throughline', outline.throughline));
  if (outline.audience) article.append(node('p', 'plan-audience', 'Audience · ' + outline.audience));
  const layout = node('div', 'plan-layout');
  const navigation = node('nav', 'plan-navigation');
  navigation.setAttribute('aria-label', 'Choose a page in the presentation plan');
  const detail = node('div', 'plan-detail');
  detail.setAttribute('role', 'region');
  detail.setAttribute('aria-label', 'Selected page plan');
  const buttons = [];
  let request = 0;
  let current = null;
  let pageFetch = null;
  signal?.addEventListener('abort', () => { ++request; pageFetch?.abort(); }, { once: true });
  async function choose(index) {
    if (current === index) return;
    const subsequent = current !== null;
    current = index;
    const identity = ++request;
    pageFetch?.abort();
    pageFetch = new AbortController();
    const slide = slides[index];
    const planned = outline.slides.find((item) => item.slide_id === slide.id);
    buttons.forEach((button, position) => button.setAttribute('aria-pressed', String(position === index)));
    detail.setAttribute('aria-busy', 'true');
    detail.replaceChildren(node('p', 'plan-loading', 'Loading the full page plan…'));
    try {
      const intent = await loadIntent(slide, pageFetch.signal);
      if (identity !== request || signal?.aborted || !article.isConnected) return;
      const heading = node('div', 'plan-page-heading');
      const title = node('div');
      title.append(node('p', 'eyebrow', 'Slide ' + String(index + 1).padStart(2, '0')), node('h4', '', planned.dominant_message));
      const show = node('button', 'plan-show-slide', 'Show slide');
      show.type = 'button';
      show.addEventListener('click', () => onShowSlide(slide));
      heading.append(title, show);
      const page = createSlideBrief(intent, { planningNotes: planned.content_obligations || [], inputs: slide.planning.inputs, signal });
      detail.replaceChildren(heading, page);
      if (subsequent && scrollContainer) requestAnimationFrame(() => {
        if (identity !== request || signal?.aborted || !heading.isConnected) return;
        const viewport = scrollContainer.getBoundingClientRect();
        const bounds = heading.getBoundingClientRect();
        if (bounds.top < viewport.top + 12 || bounds.bottom > viewport.bottom - 12) {
          scrollContainer.scrollTop += bounds.top - viewport.top - 12;
        }
      });
      announce('Planning details for slide ' + (index + 1) + '. ' + planned.dominant_message);
    } catch (error) {
      if (identity !== request || signal?.aborted || error.name === 'AbortError' || !article.isConnected) return;
      detail.replaceChildren(node('p', 'plan-error', 'The full content for this page could not be loaded. Its completed slide remains available in the presentation viewer.'));
      current = null;
    } finally {
      if (identity === request) detail.setAttribute('aria-busy', 'false');
    }
  }
  slides.forEach((slide, index) => {
    const button = node('button', 'plan-page-option');
    button.type = 'button';
    const image = new Image();
    image.src = slide.thumbnail;
    image.alt = '';
    const caption = node('span', 'plan-page-caption');
    const planned = outline.slides.find((item) => item.slide_id === slide.id);
    caption.append(node('span', 'plan-page-number', String(index + 1).padStart(2, '0')), node('span', '', planned.dominant_message));
    button.append(image, caption);
    button.setAttribute('aria-pressed', 'false');
    button.addEventListener('click', () => choose(index));
    buttons.push(button);
    navigation.append(button);
  });
  layout.append(navigation, detail);
  article.append(layout);
  const obligations = outline.shared_obligations;
  if (obligations) {
    const shared = node('div');
    if (obligations.evidence?.length) shared.append(section('Evidence', list(obligations.evidence)));
    if (obligations.exclusions?.length) shared.append(section('Exclusions', list(obligations.exclusions)));
    if (shared.childElementCount) article.append(disclosure('Presentation-wide requirements', shared));
  }
  choose(0);
  return article;
}
