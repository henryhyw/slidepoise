/* Shared profile and resource authoring. All saves use the same revisioned files as the CLI. */
let profileDocument;
const fieldNames = { hard_rules: "Design rules", design_overrides: "Style specifications", style_agency: "Creative freedom", modes: "Visual directions", asset_policy: "Images and symbols", reconstruction_guidance: "Reconstruction guidance", visual_reference_priorities: "Reference priorities", source_basis: "Sources and background", library: "Reference storage", library_sets: "Selected Library Sets", purpose: "Purpose", name: "Name" };
const fieldName = key => fieldNames[key] || key.replaceAll("_", " ").replace(/^./, c => c.toUpperCase());
function iconGlyph(fill = false) {
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 3 7.5 12 12l9-4.5L12 3Z" fill="${fill ? "currentColor" : "none"}" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="m3 12 9 4.5 9-4.5M3 16.5l9 4.5 9-4.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}
function densityIllustration(value) {
  const columns = value === "spacious" ? 1 : value === "information_rich" ? 3 : 2;
  return `<span class="density-illustration density-${columns}" aria-hidden="true"><b></b><em></em><span>${Array.from({ length: columns }, (_, i) => `<span><i></i>${"<s></s>".repeat(columns + 1)}${i === 0 ? "<u></u>" : ""}</span>`).join("")}</span></span>`;
}
function treatmentIllustration(value) {
  return `<span class="treatment-illustration ${esc(value)}" aria-hidden="true"><span>${iconGlyph()}</span><span>${iconGlyph(true)}</span></span>`;
}
function decorateChoices() {
  $$('#editor-fields input[name="density"]').forEach(input => input.nextElementSibling.insertAdjacentHTML("afterbegin", densityIllustration(input.value)));
  $$('#editor-fields input[name="icon_treatment"]').forEach(input => input.nextElementSibling.insertAdjacentHTML("afterbegin", treatmentIllustration(input.value)));
  if ($('#editor-fields input[name="primary"]')) {
    $('#editor-fields').insertAdjacentHTML("beforeend", '<div class="style-live-preview" id="palette-live"><span class="eyebrow">STYLE PREVIEW</span><div><span class="sample-icon"></span><section><h3>A clearer point of view.</h3><p>Supporting detail stays quiet and readable.</p><span class="sample-bar"></span></section></div><small>A sample of the selected color and icon treatment</small></div>');
    updateTreatmentPreview();
  }
}
function updateTreatmentPreview() {
  const preview = $('#palette-live'); if (!preview) return;
  for (const key of ["primary", "surface", "text", "background", "secondary"]) {
    const value = $(`#editor-fields input[name="${key}"]`)?.value;
    if (/^#[0-9a-f]{6}$/i.test(value)) preview.style.setProperty(`--sample-${key}`, value);
  }
  const treatment = $('#editor-fields input[name="icon_treatment"]:checked')?.value || "agent_decides";
  preview.querySelector('.sample-icon').innerHTML = iconGlyph();
  preview.dataset.treatment = treatment;
}
function readTree(value) {
  if (Array.isArray(value)) return `<ol class="guidance-list">${value.map(item => `<li>${readTree(item)}</li>`).join("")}</ol>`;
  if (value && typeof value === "object") return `<dl class="guidance-tree">${Object.entries(value).map(([key, item]) => `<div><dt>${esc(fieldName(key))}</dt><dd>${readTree(item)}</dd></div>`).join("")}</dl>`;
  if (value === null) return '<span class="muted">Open</span>';
  if (typeof value === "boolean") return `<span class="value-pill">${value ? "Yes" : "No"}</span>`;
  const text = String(value);
  return /^#[0-9a-f]{6}$/i.test(text) ? `<span class="color-value"><i style="background:${text}"></i>${text}</span>` : `<span>${esc(text)}</span>`;
}
function treeEditor(value, path = [], label = "Value") {
  if (value !== null && typeof value === "object") {
    return `<fieldset class="tree-editor"><legend>${esc(label)}</legend>${Object.entries(value).map(([key, child]) => treeEditor(child, [...path, key], Array.isArray(value) ? `Item ${Number(key) + 1}` : fieldName(key))).join("")}${!Object.keys(value).length ? '<p class="muted">Nothing added yet.</p>' : ""}</fieldset>`;
  }
  const name = esc(JSON.stringify(path));
  if (typeof value === "boolean") return `<label class="boolean-field"><input type="checkbox" name="${name}" data-tree-type="boolean" ${value ? "checked" : ""}>${esc(label)}</label>`;
  if (typeof value === "number") return `<label>${esc(label)}<input type="number" step="any" name="${name}" data-tree-type="number" value="${value}"></label>`;
  return `<label>${esc(label)}<textarea name="${name}" data-tree-type="${value === null ? "null" : "string"}" rows="${String(value || "").length > 110 ? 3 : 1}">${esc(value ?? "")}</textarea></label>`;
}
function editStructured(title, value, save, help) {
  const original = structuredClone(value);
  editor(title, `<div id="structured-fields">${treeEditor(value, [], title)}</div><details class="source-disclosureclosure"><summary>Advanced editing</summary><p class="setting-help">Changes here replace the fields above.</p><textarea id="structured-source" rows="18" spellcheck="false">${esc(JSON.stringify(value, null, 2))}</textarea></details>`, async () => {
    let result = structuredClone(original);
    const source = $('#structured-source');
    if (source.dataset.edited) result = JSON.parse(source.value);
    else for (const element of $$('#structured-fields [data-tree-type]')) {
      const path = JSON.parse(element.name);
      const type = element.dataset.treeType;
      const value = type === "boolean" ? element.checked : type === "number" ? Number(element.value) : type === "null" && !element.value ? null : element.value;
      if (!path.length) result = value;
      else { let parent = result; for (const key of path.slice(0, -1)) parent = parent[key]; parent[path.at(-1)] = value; }
    }
    await save(result);
  }, { scope: "PROFILE GUIDANCE", help });
}
async function renderProfileContents() {
  profileDocument = await api(`/api/profile?profile=${encodeURIComponent(state.design.values.profile)}`);
  const profile = profileDocument.profile;
  const references = await api(`/api/library?kind=visual_references&profile=${encodeURIComponent(profileDocument.id)}`);
  let container = $('#profile-contents');
  if (!container) { container = document.createElement('div'); container.id = 'profile-contents'; $('#design-settings').before(container); }
  const guidanceCount = Object.keys(profile).filter(key => !['profile_id', 'schema_version', 'name', 'purpose'].includes(key)).length;
  const referenceItems = references.items.map(item => `<article class="profile-reference-card"><button data-preview="${esc(item.asset_url)}" data-title="${esc(item.name || item.id)}"><img src="${esc(item.asset_url)}" alt="${esc(item.name || item.id)}"></button><span>${esc(item.name || item.id)}</span></article>`).join('');
  container.innerHTML = `<div class="profile-system-grid"><section class="profile-system-card guidance-card"><div><p class="eyebrow">PROFILE GUIDANCE</p><h3>Guidance</h3><p>Writing, layout, imagery, and design preferences for this profile.</p></div><div class="guidance-card-footer"><span>${guidanceCount} sections</span><button class="quiet-button" data-profile-workspace="guidance">Open guidance</button></div></section><section class="profile-system-card references-card"><div class="profile-card-heading"><div><p class="eyebrow">VISUAL LANGUAGE</p><h3>Visual references</h3></div><div class="inline-actions"><button class="text-button" data-add-reference>＋ Add</button><button class="quiet-button" data-profile-workspace="references">Manage</button></div></div><div class="reference-viewport">${references.count ? `<div class="profile-reference-strip">${referenceItems}</div>` : '<p class="reference-empty">Add examples that capture the look you want.</p>'}</div><span class="reference-count">${references.count} ${references.count === 1 ? 'reference' : 'references'}</span></section></div><div class="section-heading"><h3>Style settings</h3></div>`;
}
async function openProfileWorkspace() {
  profileDocument = await api(`/api/profile?profile=${encodeURIComponent(state.design.values.profile)}`);
  const profile = profileDocument.profile;
  $('#profile-title').textContent = profile.name;
  const references = await api(`/api/library?kind=visual_references&profile=${encodeURIComponent(profileDocument.id)}`);
  state.profileReferences = references;
  $('#profile-dialog-scope').textContent = 'PROFILE GUIDANCE';
  const sections = Object.entries(profile).filter(([key]) => !['profile_id', 'schema_version'].includes(key)).map(([key, value], i) => `<details class="guidance-section" ${i < 2 ? 'open' : ''}><summary>${esc(fieldName(key))}<span>${Array.isArray(value) ? value.length + ' items' : typeof value === 'object' && value ? Object.keys(value).length + ' fields' : ''}</span></summary><div class="guidance-section-body">${readTree(value)}<button class="quiet-button" data-profile-field="${esc(key)}">Edit ${esc(fieldName(key).toLowerCase())}</button></div></details>`).join('');
  $('#profile-content').innerHTML = `<p class="muted">Future presentations will use these changes. Existing presentations stay the same.</p>${sections}`;
  if (!$('#profile-dialog').open) $('#profile-dialog').showModal();
}
async function openReferencesWorkspace() {
  profileDocument = await api(`/api/profile?profile=${encodeURIComponent(state.design.values.profile)}`);
  const references = await api(`/api/library?kind=visual_references&profile=${encodeURIComponent(profileDocument.id)}`);
  state.profileReferences = references;
  $('#profile-dialog-scope').textContent = 'VISUAL REFERENCES';
  $('#profile-title').textContent = profileDocument.profile.name;
  const cards = references.items.map(item => `<article class="resource-card"><button class="resource-thumbnail" data-preview="${esc(item.asset_url)}" data-title="${esc(item.name || item.id)}"><img src="${esc(item.asset_url)}" alt="${esc(item.name || item.id)}"></button><div class="resource-copy"><h4>${esc(item.name || item.id)}</h4><p>${esc(item.description || '')}</p><button class="text-button" data-edit-reference="${esc(item.id)}">Edit guidance</button></div></article>`).join('');
  $('#profile-content').innerHTML = `<div class="reference-workspace-heading"><p>Use these examples to define the look of this profile.</p><button class="quiet-button" data-add-reference>＋ Add visual reference</button></div><div class="library-item-grid reference-editor-grid">${cards}</div>`;
  if (!$('#profile-dialog').open) $('#profile-dialog').showModal();
}
function remoteSetContents(item) {
  const remix = item.provider === 'remix_icon';
  return `<div class="remote-source-preview">${remix ? treatmentIllustration('agent_decides') : '<span class="identity-sample">W</span>'}<div><h3>${remix ? 'Line and fill in one visual family' : 'Exact identity with source details'}</h3><p>${remix ? 'Use matching line and fill icons from one consistent family.' : 'Find exact logos and public media with source and usage details.'}</p><a class="text-link" href="${remix ? 'https://remixicon.com/' : 'https://commons.wikimedia.org/'}" target="_blank" rel="noopener">Browse source ↗</a></div></div><details class="guidance-section"><summary>Source details</summary><div class="guidance-section-body">${readTree(Object.fromEntries(Object.entries(item).filter(([key]) => !['items', 'revision', 'root'].includes(key))))}</div></details>`;
}
document.addEventListener('click', event => attempt(async () => {
  const button = event.target.closest('button'); if (!button) return;
  if (button.dataset.profileWorkspace === 'guidance') return openProfileWorkspace();
  if (button.dataset.profileWorkspace === 'references') return openReferencesWorkspace();
  if (button.dataset.profileField) {
    const field = button.dataset.profileField;
    return editStructured(fieldName(field), profileDocument.profile[field], async value => {
      await api('/api/profile/update', { profile_id: profileDocument.id, revision: profileDocument.revision, values: { [field]: value } });
      await refreshOverview(); await loadDesign(); await openProfileWorkspace(); toast('Profile guidance saved');
    }, '');
  }
  if (button.hasAttribute('data-add-reference')) return editor('Add visual reference', '<label>Image<input name="file" type="file" accept=".png,.jpg,.jpeg,.webp" required></label>' + input('name', '', 'Reference name') + '<label>What should this reference influence?<textarea name="description" rows="4"></textarea></label>', async form => {
    const file = form.get('file');
    await api('/api/profile/reference/add', { profile_id: profileDocument.id, name: form.get('name'), description: form.get('description'), filename: file.name, content_base64: await fileData(file) });
    await loadDesign(); await openReferencesWorkspace(); toast('Reference added');
  }, { scope: 'PROFILE VISUAL REFERENCES', help: 'Saved to this profile.', label: 'Add reference' });
  if (button.dataset.editReference) {
    const item = state.profileReferences.items.find(item => item.id === button.dataset.editReference);
    return editStructured('Reference guidance', Object.fromEntries(Object.entries(item).filter(([key]) => !['id', 'asset_url', 'path', 'preview_path'].includes(key))), async value => {
      await api('/api/profile/reference/update', { profile_id: profileDocument.id, id: item.id, values: value, revision: state.profileReferences.revision });
      await loadDesign(); await openReferencesWorkspace(); toast('Reference guidance saved');
    }, 'Describe what to borrow and what to avoid. The image itself stays unchanged.');
  }
  if (button.dataset.newSet) return editor(`Create ${button.dataset.newSet === 'icons' ? 'Icon' : 'Component'} Set`, input('name', '', 'Set name') + '<label>Description<textarea name="description" rows="3"></textarea></label>', async form => {
    const created = await api('/api/library-set/create', { ...Object.fromEntries(form), kind: button.dataset.newSet }); await loadResources(); await openLibrarySet(created.id); toast('Set created');
  }, { scope: 'SHARED LIBRARY', label: 'Create set' });
  if (button.hasAttribute('data-edit-set')) return editor('Set details', input('name', state.openSet.name, 'Name') + `<label>Description<textarea name="description" rows="3">${esc(state.openSet.description)}</textarea></label>`, async form => {
    await api('/api/library-set/update', { set_id: state.openSet.id, revision: state.openSet.revision, values: Object.fromEntries(form) }); await loadResources(); await openLibrarySet(state.openSet.id); toast('Set updated');
  }, { scope: 'SHARED LIBRARY' });
  if (button.dataset.edit) decorateChoices();
}));
document.addEventListener('input', event => {
  if (event.target.id === 'structured-source') { event.target.dataset.edited = 'true'; $('#structured-fields').classList.add('source-overridden'); }
  if (event.target.closest('#editor-fields') && $('#palette-live')) updateTreatmentPreview();
});
document.addEventListener('change', event => { if (event.target.name === 'icon_treatment') updateTreatmentPreview(); });
