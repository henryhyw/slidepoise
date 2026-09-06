/* Inspect the retained Agent interpretation and OpenCV measurements for a slide. */
function node(tag, className, text) {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
}
function validBox(box) {
  return Array.isArray(box) && box.length === 4 && box.every(Number.isFinite) && box[2] > 0 && box[3] > 0;
}

export function reconstructionItems(semantic, measurement) {
  const width = measurement.source?.width_px;
  const height = measurement.source?.height_px;
  if (!(width > 0 && height > 0) || !Array.isArray(semantic.entities) || !Array.isArray(measurement.entities)) {
    throw new Error('The reconstruction record is incomplete.');
  }
  const measured = new Map(measurement.entities.map(item => [item.id, item]));
  const entities = semantic.entities.map(item => {
    const value = measured.get(item.id);
    if (!value) throw new Error('An interpreted object has no measurement record.');
    return {
      id: item.id, label: item.display_label || item.text || item.id, kind: item.kind,
      planned: item.bbox_hint, measured: value.measurement?.visible_bbox?.px,
      foreground: value.measurement?.color_evidence?.foreground,
      maskSource: value.measurement?.mask_source,
      lines: value.measurement?.text_geometry?.line_count_evidence,
    };
  });
  const groups = (semantic.groups || []).map(group => ({
    id: group.id, label: group.display_label || group.id, reason: group.group_reason || '',
    children: group.children || [], planned: group.bbox_hint,
  }));
  const ids = new Set(entities.map(item => item.id));
  if (ids.size !== entities.length || groups.some(group => group.children.some(id => !ids.has(id)))) {
    throw new Error('The interpretation contains inconsistent object groups.');
  }
  return { width, height, entities, groups };
}

export function createReconstructionViewer({ layer, panel, positionLayer, fetchJSON = async (url, signal) => {
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error('The reconstruction record could not be loaded.');
  return response.json();
} }) {
  let controller = null;
  function clear() {
    controller?.abort();
    controller = null;
    layer.replaceChildren();
    panel.replaceChildren();
    layer.hidden = true;
    panel.hidden = true;
  }
  async function show(slide, mode, canvas) {
    clear();
    const request = new AbortController();
    controller = request;
    panel.hidden = false;
    panel.append(node('p', '', 'Loading this slide’s reconstruction…'));
    try {
      const [semantic, measurement] = await Promise.all([
        fetchJSON(slide.semantic, request.signal), fetchJSON(slide.measurement, request.signal),
      ]);
      if (request.signal.aborted) return;
      const data = reconstructionItems(semantic, measurement);
      const measuring = mode === 'measurements';
      panel.replaceChildren();
      positionLayer(layer, canvas);
      layer.hidden = false;
      layer.dataset.mode = mode;
      panel.append(node('p', 'reconstruction-intro', measuring
        ? 'OpenCV locates visible ink within the regions identified by the Agent. Select an element to see its pixel measurements.'
        : 'The Agent identifies the text, charts, artwork and relationships needed to rebuild this page. Outlines show its planned object regions.'));
      const controls = node('div', 'reconstruction-groups');
      const detail = node('p', 'reconstruction-detail');
      detail.setAttribute('aria-live', 'polite');
      const boxes = new Map();
      const all = node('button', '', `All ${data.entities.length} elements`);
      all.type = 'button';
      all.setAttribute('aria-pressed', 'true');
      controls.append(all);
      function select(ids, description) {
        for (const [id, box] of boxes) {
          box.dataset.selected = String(ids.includes(id));
          box.dataset.dimmed = String(ids.length > 0 && !ids.includes(id));
        }
        detail.textContent = description;
      }
      all.addEventListener('click', () => {
        controls.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed', String(button === all)));
        select([], `${data.entities.length} interpreted elements · ${data.groups.length} authored groups · ${data.width} × ${data.height} px source image`);
      });
      if (!measuring) data.groups.forEach(group => {
        const button = node('button', '', group.label);
        button.type = 'button';
        button.setAttribute('aria-pressed', 'false');
        button.addEventListener('click', () => {
          controls.querySelectorAll('button').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
          select(group.children, `${group.label}. ${group.reason} ${group.children.length} elements.`);
        });
        controls.append(button);
      });
      data.entities.forEach(item => {
        const box = measuring ? item.measured : item.planned;
        if (!validBox(box)) return;
        const [x, y, width, height] = box;
        const button = node('button', 'reconstruction-box');
        button.type = 'button';
        button.setAttribute('aria-label', `${item.kind || 'Element'}. ${item.label}`);
        button.title = item.label;
        Object.assign(button.style, {left: `${100*x/data.width}%`, top: `${100*y/data.height}%`, width: `${100*width/data.width}%`, height: `${100*height/data.height}%`, zIndex: String(Math.max(1, 1000 - Math.round(999 * width * height / (data.width * data.height))))});
        button.addEventListener('click', () => {
          controls.querySelectorAll('button').forEach(control => control.setAttribute('aria-pressed', 'false'));
          const coordinates = `x ${x}, y ${y}, width ${width}, height ${height} px`;
          const extra = measuring ? [item.foreground && `ink ${item.foreground}`, item.lines && `${item.lines} text line${item.lines === 1 ? '' : 's'}`].filter(Boolean).join(' · ') : item.kind;
          select([item.id], `${item.label} · ${coordinates}${extra ? ` · ${extra}` : ''}`);
        });
        boxes.set(item.id, button);
        layer.append(button);
      });
      panel.append(controls, detail);
      all.click();
    } catch (error) {
      if (request.signal.aborted) return;
      panel.replaceChildren(node('p', '', 'This slide’s reconstruction record could not be loaded.'));
      const retry = node('button', 'reconstruction-retry', 'Try again');
      retry.type = 'button';
      retry.addEventListener('click', () => show(slide, mode, canvas));
      panel.append(retry);
    }
  }
  return { show, clear };
}
