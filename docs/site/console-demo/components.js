let componentDocument;
let selectedObject;
function componentSymbol(asset) {
  const type = asset.constructor_defaults?.chart_structure?.type || asset.kind || '';
  if (type.includes('doughnut')) return '<svg viewBox="0 0 160 90" aria-hidden="true"><circle cx="80" cy="45" r="29" fill="none" stroke="#eee9e4" stroke-width="13"/><circle cx="80" cy="45" r="29" fill="none" stroke="#e96728" stroke-width="13" stroke-dasharray="115 190" transform="rotate(-90 80 45)"/></svg>';
  return `<svg viewBox="0 0 160 90" aria-hidden="true">${[0, 1, 2, 3].map((n) => type.includes('table') || asset.kind === 'table' ? `<rect x="${14 + n * 34}" y="20" width="30" height="12" fill="#e96728"/><rect x="${14 + n * 34}" y="37" width="30" height="35" fill="#eee9e4"/>` : `<rect x="${24 + n * 29}" y="${55 - n * 10}" width="18" height="${20 + n * 10}" fill="${n === 3 ? '#e96728' : '#d9d6d2'}"/>`).join('')}</svg>`;
}
const svgText = (x, y, text, size = 12, color = '#242321', extra = '') => `<text x="${x}" y="${y}" font-size="${size}" fill="${esc(color)}" ${extra}>${esc(text)}</text>`;
function chartSvg(chart, width, height) {
  const colors = chart.series.map((entry, i) => entry.color || ['#ed6b2d', '#f2a877', '#777777', '#bababa'][i % 4]);
  const font = Math.max(8, Math.min(14, height / 22));
  const title = chart.title ? svgText(14, font + 6, chart.title, font * 1.15) : '';
  const top = chart.title ? font * 3 : 18;
  const plotH = Math.max(20, height - top - font * (chart.show_legend ? 5 : 3));
  const plotW = width - 70;
  let body = '';
  const pointColor = i => chart.series[0]?.point_colors?.[i] || ['#ed6b2d', '#f38f54', '#f8b78d', '#9ba0a6'][i % 4];
  const type = chart.type;
  if (/DOUGHNUT|PIE/.test(type)) {
    const values = chart.series[0]?.values || [];
    const sum = values.reduce((a, b) => a + Math.max(0, b || 0), 0) || 1;
    const radius = Math.max(10, Math.min(plotW, plotH) / 2.3), cx = width * .38, cy = top + plotH / 2;
    let angle = -Math.PI / 2;
    values.forEach((value, i) => {
      const end = angle + Math.max(0, value || 0) / sum * Math.PI * 2;
      const x1 = cx + radius * Math.cos(angle), y1 = cy + radius * Math.sin(angle);
      const x2 = cx + radius * Math.cos(end - .00001), y2 = cy + radius * Math.sin(end - .00001);
      body += `<path d="M${cx},${cy} L${x1},${y1} A${radius},${radius} 0 ${end - angle > Math.PI ? 1 : 0},1 ${x2},${y2} Z" fill="${pointColor(i)}"/>`;
      angle = end;
    });
    if (type.includes('DOUGHNUT')) body += `<circle cx="${cx}" cy="${cy}" r="${radius * (chart.hole_size || 60) / 100}" fill="white"/>`;
    if (chart.show_legend) chart.categories.forEach((label, i) => { body += `<rect x="${width * .7}" y="${top + i * font * 2}" width="${font}" height="${font}" fill="${pointColor(i)}"/>${svgText(width * .7 + font * 1.5, top + font + i * font * 2, label, font)}`; });
    return title + body;
  }
  const stacked = /STACKED/.test(type);
  const percent = /100/.test(type);
  const valuesAt = (n, s) => Number(chart.series[s]?.values[n]) || 0;
  const all = chart.categories.map((_, n) => chart.series.map((_, s) => valuesAt(n, s)));
  const max = percent ? 100 : Math.max(1, ...all.flat(), ...(stacked ? all.map(row => row.filter(v => v > 0).reduce((a, b) => a + b, 0)) : []));
  const min = percent ? 0 : Math.min(0, ...all.flat(), ...(stacked ? all.map(row => row.filter(v => v < 0).reduce((a, b) => a + b, 0)) : []));
  const scale = value => plotH - (value - min) / (max - min) * plotH;
  const y0 = top + scale(0), count = Math.max(1, chart.categories.length);
  if (type.startsWith('BAR_')) {
    const left = Math.min(100, width * .25), usable = width - left - 24;
    const xAt = value => left + (value - min) / (max - min) * usable;
    chart.categories.forEach((label, n) => {
      const step = plotH / count, y = top + n * step;
      body += svgText(left - 9, y + step / 2 + font / 3, label, font, '#666', 'text-anchor="end"');
      let positive = 0, negative = 0;
      const sum = all[n].reduce((a, b) => a + Math.abs(b), 0) || 1;
      chart.series.forEach((entry, s) => {
        const value = percent ? valuesAt(n, s) / sum * 100 : valuesAt(n, s);
        const start = stacked ? value < 0 ? negative : positive : 0, end = start + value;
        if (value < 0) negative = end; else positive = end;
        const bh = step * .65 / (stacked ? 1 : chart.series.length);
        body += `<rect x="${Math.min(xAt(start), xAt(end))}" y="${y + step * .17 + (stacked ? 0 : s * bh)}" width="${Math.max(.5, Math.abs(xAt(end) - xAt(start)))}" height="${bh}" fill="${colors[s]}"/>`;
      });
    });
    if (chart.show_legend) chart.series.forEach((entry, i) => { body += svgText(14 + i * (width - 24) / chart.series.length, height - 8, `● ${entry.name}`, font * .85, colors[i]); });
    return title + body;
  }
  for (let i = 0; i < 5; i++) { const v = min + (max - min) * i / 4, y = top + scale(v); body += `<path d="M42 ${y}H${width - 18}" stroke="#e7e7e7"/>${svgText(36, y + 3, Math.round(v * 100) / 100, font * .8, '#777', 'text-anchor="end"')}`; }
  if (/LINE|AREA/.test(type)) {
    chart.series.forEach((entry, s) => {
      const points = chart.categories.map((_, n) => [42 + (n + .5) * plotW / count, top + scale(valuesAt(n, s))]);
      if (type.includes('AREA')) body += `<polygon points="${[[points[0]?.[0] || 42, y0], ...points, [points.at(-1)?.[0] || 42, y0]].map(p => p.join(',')).join(' ')}" fill="${colors[s]}" fill-opacity=".45"/>`;
      body += `<polyline points="${points.map(p => p.join(',')).join(' ')}" fill="none" stroke="${colors[s]}" stroke-width="2"/>`;
    });
  } else {
    chart.categories.forEach((_, n) => {
      let positive = 0, negative = 0;
      const sum = all[n].reduce((a, b) => a + Math.abs(b), 0) || 1;
      chart.series.forEach((entryentry, s) => {
        let value = valuesAt(n, s); if (percent) value = value / sum * 100;
        const start = stacked ? value < 0 ? negative : positive : 0;
        const end = start + value;
        if (value < 0) negative = end; else positive = end;
        const step = plotW / count, barW = step * .65 / (stacked ? 1 : chart.series.length);
        const x = 42 + n * step + step * .17 + (stacked ? 0 : s * barW);
        const y = top + Math.min(scale(start), scale(end)), h = Math.max(.5, Math.abs(scale(start) - scale(end)));
        body += `<rect x="${x}" y="${y}" width="${barW}" height="${h}" fill="${chart.series.length === 1 ? pointColor(n) : colors[s]}"/>`;
      });
    });
  }
  chart.categories.forEach((label, i) => { body += svgText(42 + (i + .5) * plotW / count, top + plotH + font * 1.6, label, font * .85, '#555', 'text-anchor="middle"'); });
  if (chart.show_legend) chart.series.forEach((entry, i) => { body += svgText(42 + i * plotW / chart.series.length, height - 8, `● ${entry.name}`, font * .85, colors[i]); });
  return title + body;
}
function nativeObjectSvg(object) {
  const { width: w, height: h } = object;
  let content = '';
  if (object.type === 'group') {
    const space = object.child_space || [0, 0, w, h];
    content = `<g transform="scale(${w / (space[2] || w)} ${h / (space[3] || h)}) translate(${-space[0]} ${-space[1]})">${object.children.map(nativeObjectSvg).join('')}</g>`;
  } else if (object.type === 'chart') content = chartSvg(object.chart, w, h);
  else if (object.type === 'image') content = `<image href="${esc(object.image)}" width="${w}" height="${h}" preserveAspectRatio="none"/>`;
  else if (object.type === 'table') {
    let y = 0;
    object.cells.forEach((row, r) => {
      let x = 0;
      row.forEach((cell, c) => {
        const cw = object.column_widths[c], ch = object.row_heights[r];
        if (!cell.merged) {
          const spanW = object.column_widths.slice(c, c + cell.col_span).reduce((a, b) => a + b, 0), spanH = object.row_heights.slice(r, r + cell.row_span).reduce((a, b) => a + b, 0);
          content += `<rect x="${x}" y="${y}" width="${spanW}" height="${spanH}" fill="${cell.fill || (r === 0 ? '#eaeaea' : '#fff')}" stroke="#d6d6d6" stroke-width=".5"/>${svgText(x + 5, y + Math.min(spanH - 3, cell.font_size || 12) + 3, cell.text, cell.font_size || 11, cell.color || '#222')}`;
        }
        x += cw;
      }); y += object.row_heights[r];
    });
  } else {
    const paint = `fill="${object.fill || 'none'}" stroke="${object.line || 'none'}"`;
    content = object.geometry === 'OVAL' ? `<ellipse cx="${w / 2}" cy="${h / 2}" rx="${w / 2}" ry="${h / 2}" ${paint}/>` : `<rect width="${w}" height="${h}" ${paint}/>`;
    let y = 0;
    for (const paragraph of object.paragraphs || []) {
      const first = paragraph.runs[0] || {}, size = first.font_size || paragraph.font_size || 14;
      y += size * 1.2;
      content += svgText(3, y, paragraph.text, size, first.color || paragraph.color || '#222', `font-family="${esc(first.font || paragraph.font || 'Arial')}" font-weight="${first.bold || paragraph.bold ? 'bold' : 'normal'}"`);
    }
  }
  return `<g transform="translate(${object.x} ${object.y}) rotate(${object.rotation || 0} ${w / 2} ${h / 2})" data-native-object="${esc(object.id)}" tabindex="0" role="button" aria-label="${esc(object.name)}"><title>${esc(object.name)} · ${esc(object.type)}</title>${content}<rect class="object-hitbox ${selectedObject?.id === object.id ? 'selected' : ''}" width="${w}" height="${h}"/></g>`;
}
function allNativeObjects(objects) { return objects.flatMap(object => [object, ...allNativeObjects(object.children || [])]); }
function renderNativeStage() {
  const doc = componentDocument;
  $('#native-stage').innerHTML = `<svg viewBox="0 0 ${doc.width} ${doc.height}" aria-label="Live native object preview"><rect width="${doc.width}" height="${doc.height}" fill="${doc.background}"/>${doc.objects.map(nativeObjectSvg).join('')}</svg>`;
}
async function openComponent(id, slide) {
  componentDocument = await api(`/api/component?set_id=${encodeURIComponent(state.openSet.id)}&id=${encodeURIComponent(id)}${slide ? '&slide=' + slide : ''}`);
  selectedObject = null;
  renderComponent();
  if (!$('#component-dialog').open) $('#component-dialog').showModal();
}
function renderComponent() {
  const doc = componentDocument, component = doc.component;
  $('#component-title').textContent = component.name || component.id;
  $('#component-content').innerHTML = `<div class="collection-intro"><p>${esc(component.description || '')}</p><div class="inline-actions"><button class="quiet-button" data-component-guidance>Edit component guidance</button>${doc.native ? `<button class="quiet-button" data-open-native>Open in PowerPoint ↗</button><a class="text-link" href="/api/component/source?set_id=${encodeURIComponent(doc.set_id)}&id=${encodeURIComponent(component.id)}" download>Download PPTX</a>` : ''}</div></div>${doc.native ? `<div class="native-workspace"><div><div class="native-toolbar"><span>Source slide ${doc.slide_number} of ${doc.slide_count}</span><div><button class="text-button" data-native-slide="${doc.slide_number - 1}" ${doc.slide_number <= 1 ? 'disabled' : ''} aria-label="Previous source slide">‹</button><button class="text-button" data-native-slide="${doc.slide_number + 1}" ${doc.slide_number >= doc.slide_count ? 'disabled' : ''} aria-label="Next source slide">›</button></div></div><div id="native-stage"></div><p class="setting-help">This preview uses the component’s editable objects and data. Open it in PowerPoint for the final type and chart rendering.</p><div class="native-object-list">${allNativeObjects(doc.objects).map(object => `<button class="native-object-row" data-select-native="${esc(object.id)}"><span>${esc(object.type)}</span><strong>${esc(object.name)}</strong><small>${Math.round(object.width)} × ${Math.round(object.height)} pt</small></button>`).join('')}</div></div><aside id="native-inspector"><h3>Inside the component</h3><p>Choose an object to edit its position, content, or data.</p><p class="setting-help">Changes update the shared PowerPoint component. A backup is saved first.</p></aside></div>` : `<div class="grammar-notice"><h3>Design grammar</h3><p>${esc(doc.note)}</p><p>This definition describes how to build the component with editable PowerPoint objects.</p></div>`}<details class="guidance-section"><summary>Component details</summary><div class="guidance-section-body">${readTree(component)}</div></details>`;
  if (doc.native) renderNativeStage();
}
function inspectNativeObject(id) {
  selectedObject = allNativeObjects(componentDocument.objects).find(object => object.id === id);
  const item = selectedObject, first = item.paragraphs?.[0], run = first?.runs?.[0];
  $('#native-inspector').innerHTML = `<form id="native-object-form"><p class="eyebrow">${esc(item.type).toUpperCase()}</p><h3>${esc(item.name)}</h3>${input('name', item.name, 'Object name')}<fieldset><legend>Geometry · points</legend><div class="geometry-inputs">${['x', 'y', 'width', 'height', 'rotation'].map(key => `<label>${fieldName(key)}<input type="number" step="any" name="${key}" value="${item[key]}"></label>`).join('')}</div></fieldset>${item.text !== undefined ? `<label>Text<textarea name="text" rows="4">${esc(item.text)}</textarea></label>${input('font', run?.font || first?.font || '', 'Typeface')}${input('font_size', run?.font_size || first?.font_size || '', 'Size · pt', 'number')}` : ''}${item.type === 'shape' || item.type === 'text' ? input('fill', item.fill || '', 'Fill · hex, blank keeps source') + input('line', item.line || '', 'Outline · hex, blank keeps source') : ''}${item.type === 'chart' ? `<fieldset><legend>Chart data</legend><p class="setting-help">${esc(item.chart.type.replaceAll('_', ' ').toLowerCase())}</p>${item.chart.editable_data ? `<button type="button" class="quiet-button" data-edit-chart>Edit data & chart properties</button>` : '<p>Edit this chart type in PowerPoint.</p>'}</fieldset>` : ''}${item.type === 'table' ? '<fieldset><legend>Table contents</legend><button type="button" class="quiet-button" data-edit-table>Edit cells</button></fieldset>' : ''}<p id="native-save-error" class="error-message" hidden></p><button class="primary-button" type="submit">Save object to PPTX</button></form><details class="guidance-section"><summary>All inspected properties</summary><div class="guidance-section-body">${readTree(Object.fromEntries(Object.entries(item).filter(([key]) => key !== 'image')))}</div></details>`;
  renderNativeStage();
}
async function saveNativeValues(values) {
  const id = selectedObject.id;
  componentDocument = await api('/api/component/object', { set_id: componentDocument.set_id, id: componentDocument.component.id, object_id: id, slide_number: componentDocument.slide_number, revision: componentDocument.source_revision, values });
  renderComponent(); inspectNativeObject(id); toast('Saved to the native PowerPoint');
}
document.addEventListener('click', event => attempt(async () => {
  const hit = event.target.closest('[data-native-object]');
  if (hit) return inspectNativeObject(hit.dataset.nativeObject);
  const button = event.target.closest('button'); if (!button) return;
  if (button.dataset.component) return openComponent(button.dataset.component);
  if (button.dataset.selectNative) return inspectNativeObject(button.dataset.selectNative);
  if (button.dataset.nativeSlide) return openComponent(componentDocument.component.id, Number(button.dataset.nativeSlide));
  if (button.hasAttribute('data-open-native')) return api('/api/component/open', { set_id: componentDocument.set_id, id: componentDocument.component.id });
  if (button.hasAttribute('data-component-guidance')) return editStructured('Component guidance', Object.fromEntries(Object.entries(componentDocument.component).filter(([key]) => !['id', 'path', 'preview_path', 'native_source_slide_number'].includes(key))), async values => {
    await api('/api/component/definition', { set_id: componentDocument.set_id, id: componentDocument.component.id, revision: componentDocument.catalog_revision, values }); await openComponent(componentDocument.component.id); toast('Component guidance saved');
  }, 'Shared across every profile using this set. Native source identity is preserved.');
  if (button.hasAttribute('data-edit-chart')) return editStructured('Chart data & properties', selectedObject.chart, async chart => saveNativeValues({ chart }), 'Chart values update both the native chart and its embedded Excel workbook.');
  if (button.hasAttribute('data-edit-table')) return editStructured('Table cells', selectedObject.cells.map(row => row.map(cell => ({ text: cell.text }))), async cells => saveNativeValues({ cells }), 'Edit cell contents here. Use PowerPoint for merged cells, row counts and detailed styling.');
}));
document.addEventListener('submit', event => {
  if (event.target.id !== 'native-object-form') return;
  event.preventDefault();
  const button = event.target.querySelector('[type="submit"]'); button.disabled = true;
  const values = Object.fromEntries(new FormData(event.target));
  for (const key of ['x', 'y', 'width', 'height', 'rotation', 'font_size']) { if (values[key] !== undefined && values[key] !== '') values[key] = Number(values[key]); else delete values[key]; }
  for (const key of ['font', 'fill', 'line']) if (!values[key]) delete values[key];
  saveNativeValues(values).catch(error => { $('#native-save-error').textContent = error.message; $('#native-save-error').hidden = false; }).finally(() => { button.disabled = false; });
});
