/* Profiles store selections. Every resource stays in its shared set. */
const resourceKinds = { visual_references: 'Visual references', icons: 'Icons', components: 'Components' };
let resourcePicker = null;

function resourceSelection(profile, sets) {
  return Object.fromEntries(sets.map(set => [set.id, {
    enabled: (profile.library_sets?.[set.kind] || []).includes(set.id),
    ids: Object.hasOwn(profile.library_items?.[set.kind] || {}, set.id) ? [...profile.library_items[set.kind][set.id]] : null,
  }]));
}
function selectedResourceValues(selection, sets) {
  const library_sets = Object.fromEntries(Object.keys(resourceKinds).map(kind => [kind, []]));
  const library_items = Object.fromEntries(Object.keys(resourceKinds).map(kind => [kind, {}]));
  for (const set of sets) {
    const choice = selection[set.id];
    if (!choice.enabled) continue;
    library_sets[set.kind].push(set.id);
    if (choice.ids !== null) library_items[set.kind][set.id] = [...choice.ids];
  }
  return { library_sets, library_items };
}
function toggleResourceItem(choice, items, itemId, checked) {
  const ids = new Set(choice.enabled ? (choice.ids === null ? items.map(item => item.id) : choice.ids) : []);
  if (checked) ids.add(itemId); else ids.delete(itemId);
  return { enabled: ids.size > 0, ids: [...ids] };
}
function selectionSummary(set) {
  const choice = resourcePicker.selection[set.id];
  if (!choice.enabled) return 'Not selected';
  if (set.source === 'remote') return 'Available for retrieval';
  return choice.ids === null ? 'All items, including future additions' : `${choice.ids.length} selected items`;
}
async function openResourcePicker(kind = 'visual_references') {
  const [profile, catalog] = await Promise.all([
    api(`/api/profile?profile=${encodeURIComponent(state.consoleProfile || state.overview.active_profile)}`),
    api('/api/library-sets'),
  ]);
  resourcePicker = { profile, sets: catalog.sets, selection: resourceSelection(profile.profile, catalog.sets), kind, expanded: new Set(), catalogs: {}, query: '' };
  $('#resource-picker-title').textContent = `Resources for ${profile.profile.name}`;
  $('#resource-picker-error').hidden = true;
  renderResourcePicker();
  if (!$('#resources-dialog').open) $('#resources-dialog').showModal();
}
function pickerSet(set) {
  const choice = resourcePicker.selection[set.id];
  const expanded = resourcePicker.expanded.has(set.id);
  return `<section class="picker-set ${choice.enabled ? 'selected' : ''}" data-picker-set="${esc(set.id)}"><div class="picker-set-heading"><label class="picker-set-check"><input type="checkbox" data-select-set="${esc(set.id)}" ${choice.enabled ? 'checked' : ''}><span><strong>${esc(set.name)}</strong><small>${esc(set.description)}</small><em data-selection-summary="${esc(set.id)}">${esc(selectionSummary(set))}</em></span></label>${set.source === 'remote' ? '<span class="set-source">Online source</span>' : `<button type="button" class="quiet-button" data-expand-set="${esc(set.id)}" aria-expanded="${expanded}">${expanded ? 'Hide items' : 'Choose items'}</button>`}</div><div class="picker-set-items" data-picker-items="${esc(set.id)}" ${expanded ? '' : 'hidden'}>${expanded ? pickerSetItems(set) : ''}</div></section>`;
}
function pickerSetItems(set) {
  const catalog = resourcePicker.catalogs[set.id];
  if (!catalog) return '<p class="muted" role="status">Loading resources…</p>';
  const choice = resourcePicker.selection[set.id];
  return `<div class="picker-item-tools"><button type="button" class="text-button" data-all-items="${esc(set.id)}">Use all, including future additions</button><button type="button" class="text-button" data-clear-items="${esc(set.id)}">Clear selection</button></div><label class="picker-search">Find in this set<input type="search" data-item-query="${esc(set.id)}" placeholder="Search names, descriptions, or tags"></label><div class="picker-item-grid ${set.kind}" data-picker-grid="${esc(set.id)}">${catalog.items.map(item => {
    const checked = choice.enabled && (choice.ids === null || choice.ids.includes(item.id));
    const search = [item.name, item.description, ...(item.tags || [])].join(' ').toLowerCase();
    return `<label class="picker-item" data-item-search="${esc(search)}"><input type="checkbox" data-select-item="${esc(item.id)}" data-item-set="${esc(set.id)}" ${checked ? 'checked' : ''}>${item.asset_url ? `<img loading="lazy" src="${esc(item.asset_url)}" alt="">` : '<span class="picker-item-symbol" aria-hidden="true">▦</span>'}<span><strong>${esc(item.name || item.id)}</strong>${set.kind === 'visual_references' && item.description ? `<small>${esc(item.description)}</small>` : ''}</span></label>`;
  }).join('') || '<p class="muted">This set has no items yet. Add resources in Resources.</p>'}</div>`;
}
function renderResourcePicker() {
  $('#resource-picker-tabs').innerHTML = Object.entries(resourceKinds).map(([kind, name]) => `<button type="button" role="tab" id="resource-tab-${kind}" aria-selected="${resourcePicker.kind === kind}" aria-controls="resource-picker-content" data-resource-kind="${kind}">${name}<span>${resourcePicker.sets.filter(set => set.kind === kind && resourcePicker.selection[set.id].enabled).length}</span></button>`).join('');
  $('#resource-picker-content').setAttribute('aria-labelledby', `resource-tab-${resourcePicker.kind}`);
  const sets = resourcePicker.sets.filter(set => set.kind === resourcePicker.kind);
  $('#resource-picker-content').innerHTML = sets.map(pickerSet).join('') || empty('No shared sets yet', 'Add a set in Resources. It will be available to every profile.');
  updatePickerSummary();
}
function updatePickerSummary() {
  const values = selectedResourceValues(resourcePicker.selection, resourcePicker.sets);
  const total = Object.values(values.library_sets).reduce((count, ids) => count + ids.length, 0);
  $('#resource-picker-summary').textContent = `${total} shared ${total === 1 ? 'set' : 'sets'} selected`;
  for (const set of resourcePicker.sets) {
    const label = $(`[data-selection-summary="${CSS.escape(set.id)}"]`);
    if (label) label.textContent = selectionSummary(set);
    const checkbox = $(`[data-select-set="${CSS.escape(set.id)}"]`);
    if (checkbox) {
      checkbox.checked = resourcePicker.selection[set.id].enabled;
      checkbox.closest('.picker-set').classList.toggle('selected', checkbox.checked);
    }
  }
  $$('[data-resource-kind]').forEach(button => {
    button.querySelector('span').textContent = resourcePicker.sets.filter(set => set.kind === button.dataset.resourceKind && resourcePicker.selection[set.id].enabled).length;
  });
}
function refreshPickerSet(setId) {
  const set = resourcePicker.sets.find(set => set.id === setId);
  const container = $(`[data-picker-items="${CSS.escape(setId)}"]`);
  if (container && resourcePicker.expanded.has(setId)) container.innerHTML = pickerSetItems(set);
  updatePickerSummary();
}
async function loadResources() {
  state.librarySets = await api('/api/library-sets');
  const profileId = state.consoleProfile || state.overview.active_profile;
  const selectedProfile = state.overview.profiles.find(profile => profile.id === profileId);
  const profileControl = `<section class="resource-profile-bar" aria-label="Profile resource selection"><div class="resource-profile-copy"><h3>Resources for your presentations</h3><p>Choose the references, icons and components the Agent can use with this profile.</p></div><div class="resource-profile-actions"><details class="resource-profile-picker"><summary id="resource-profile"><span><small>Profile</small><strong>${esc(selectedProfile?.name || profileId)}</strong></span><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></summary><div class="resource-profile-options" role="group" aria-label="Choose a profile">${state.overview.profiles.map(profile => `<button type="button" data-resource-profile-choice="${esc(profile.id)}" aria-pressed="${profile.id === profileId}"><span><strong>${esc(profile.name)}</strong></span><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg></button>`).join('')}</div></details><button class="primary-button" data-choose-resources="visual_references">Choose available resources</button></div></section><div class="shared-library-heading"><h3>Shared library</h3><p>All collections are listed below. Editing a collection updates it for every profile that uses it.</p></div>`;
  $('#library-grid').innerHTML = profileControl + Object.entries(resourceKinds).map(([kind, name]) => {
    const sets = state.librarySets.sets.filter(set => set.kind === kind);
    return `<section class="library-group"><div class="library-group-heading"><span class="collection-symbol">${kind === 'icons' ? iconGlyph() : kind === 'visual_references' ? '▧' : '▦'}</span><div><h3>${name}</h3><p>${sets.length} shared ${sets.length === 1 ? 'set' : 'sets'}</p></div><button class="icon-button add-set-button" data-new-set="${kind}" aria-label="Add ${name.toLowerCase()} set">＋</button></div><div class="set-list">${sets.map(set => `<button class="set-row" data-library-set="${esc(set.id)}"><span class="set-source">${set.source === 'remote' ? 'Online' : 'Local'}</span><span><strong>${esc(set.name)}</strong><small>${esc(set.description)}</small></span><b>›</b></button>`).join('') || '<p class="muted">Add your first set. Profiles can choose the resources they need.</p>'}</div></section>`;
  }).join('');
}
async function openLibrarySet(setId) {
  state.openSet = await api(`/api/library-set?set_id=${encodeURIComponent(setId)}`);
  const item = state.openSet;
  $('#library-title').textContent = item.name;
  const cards = item.kind === 'visual_references' ? referenceCards(item.items) : item.items.map(asset => item.kind === 'components' ? `<button class="resource-card native-tile" data-component="${esc(asset.id)}"><div class="native-mini">${componentSymbol(asset)}</div><div class="resource-copy"><span class="eyebrow">${asset.path?.endsWith('.pptx') ? 'EDITABLE POWERPOINT' : 'DESIGN GUIDANCE'}</span><h4>${esc(asset.name || asset.id)}</h4><p>${esc(asset.description || '')}</p><span class="text-link">Inspect component</span></div></button>` : `<article class="resource-card"><button class="resource-thumbnail" data-preview="${esc(asset.asset_url || '')}" data-title="${esc(asset.name || asset.id)}"><img loading="lazy" src="${esc(asset.asset_url || '')}" alt="${esc(asset.name || asset.id)}"></button><div class="resource-copy"><h4>${esc(asset.name || asset.id)}</h4><p>${esc(asset.description || '')}</p><button class="text-button" data-edit-shared-item="${esc(asset.id)}">Edit details</button></div></article>`).join('');
  $('#library-detail').innerHTML = `<div class="collection-intro"><p>${esc(item.description)}</p><p class="setting-help">Shared by every profile that selects this set or its items.</p><div class="inline-actions"><button class="text-button" data-edit-set>Set details</button>${item.source === 'local' ? '<button class="quiet-button" id="add-set-resource">＋ Add resource</button>' : ''}</div></div>${item.source === 'remote' ? remoteSetContents(item) : `<label class="shared-set-search">Find in this set<input type="search" id="shared-set-query" placeholder="Search names, descriptions, or tags"></label><p id="shared-set-count" class="setting-help">${item.items.length} resources</p><div class="library-item-grid ${item.kind === 'visual_references' ? 'reference-editor-grid' : ''}" id="shared-set-items">${cards || empty('No resources yet', 'Add a file to make it available for selection.')}</div>`}`;
  if (!$('#library-dialog').open) $('#library-dialog').showModal();
}
function resourceSourceFields() {
  return '<label>Origin<select name="source_type"><option value="unknown">Unclassified</option><option value="published_document">Published document</option><option value="user_private_document">My original reference</option><option value="generated_image">AI-generated image</option></select></label>' + input('source_page', '', 'Source page or image locator');
}
function addSharedResource() {
  const set = state.openSet;
  const accept = { visual_references: '.png,.jpg,.jpeg,.webp', icons: '.svg,.png', components: '.pptx,.json,.svg,.png' }[set.kind];
  return editor('Add shared resource', `<label>File<input type="file" name="file" accept="${accept}" required></label>` + input('name', '', 'Name') + '<label>Description<textarea name="description" rows="3"></textarea></label>' + input('tags', '', 'Search terms, separated by commas') + (set.kind === 'visual_references' ? resourceSourceFields() : '') + input('source_url', '', 'Source URL or document name') + input('license', '', 'Usage or attribution notes'), async form => {
    const values = Object.fromEntries(form); const file = values.file; delete values.file;
    values.tags = values.tags.split(',').map(tag => tag.trim()).filter(Boolean);
    await api('/api/library-set/add', { ...values, set_id: set.id, filename: file.name, content_base64: await fileData(file) });
    await openLibrarySet(set.id); toast('Shared resource added');
  }, { scope: set.name.toUpperCase(), help: 'Profiles using the whole set receive new items automatically. Icons require usage information.', label: 'Add resource' });
}
function editSharedResource(item) {
  return editStructured(item.set_id && state.openSet?.kind === 'icons' ? 'Resource details' : 'Reference guidance', Object.fromEntries(Object.entries(item).filter(([key]) => !['id', 'asset_id', 'component_id', 'resource_id', 'set_id', 'path', 'file', 'preview', 'preview_path', 'definition_path', 'asset_url', 'catalog_revision'].includes(key))), async value => {
    await api('/api/library-set/item/update', { set_id: item.set_id, id: item.id, values: value, revision: item.catalog_revision });
    if ($('#library-dialog').open) await openLibrarySet(item.set_id);
    if (state.consoleProfile) await loadDesign();
    if ($('#profile-dialog').open) await openReferencesWorkspace();
    toast('Shared resource updated');
  }, 'Changes apply to every profile using this resource.');
}

document.addEventListener('click', event => attempt(async () => {
  const chooser = $('.resource-profile-picker');
  if (chooser && !chooser.contains(event.target)) chooser.open = false;
  const button = event.target.closest('button'); if (!button) return;
  if (button.dataset.resourceProfileChoice) {
    state.consoleProfile = button.dataset.resourceProfileChoice;
    await loadResources();
    $('#resource-profile').focus();
    return;
  }
  if (button.hasAttribute('data-choose-resources')) return openResourcePicker(button.dataset.chooseResources || 'visual_references');
  if (button.dataset.resourceKind) { resourcePicker.kind = button.dataset.resourceKind; return renderResourcePicker(); }
  if (button.dataset.expandSet) {
    const id = button.dataset.expandSet;
    if (resourcePicker.expanded.has(id)) resourcePicker.expanded.delete(id);
    else resourcePicker.expanded.add(id);
    renderResourcePicker();
    if (resourcePicker.expanded.has(id) && !resourcePicker.catalogs[id]) {
      const picker = resourcePicker;
      const catalog = await api(`/api/library-set?set_id=${encodeURIComponent(id)}`);
      if (picker !== resourcePicker) return;
      picker.catalogs[id] = catalog;
      refreshPickerSet(id);
    }
  }
  if (button.dataset.allItems) { resourcePicker.selection[button.dataset.allItems] = { enabled: true, ids: null }; return refreshPickerSet(button.dataset.allItems); }
  if (button.dataset.clearItems) { resourcePicker.selection[button.dataset.clearItems] = { enabled: false, ids: [] }; return refreshPickerSet(button.dataset.clearItems); }
  if (button.dataset.editSharedItem) return editSharedResource(state.openSet.items.find(item => item.id === button.dataset.editSharedItem));
}));
document.addEventListener('change', event => {
  const input = event.target;
  if (input.dataset.selectSet) {
    resourcePicker.selection[input.dataset.selectSet] = { enabled: input.checked, ids: null };
    refreshPickerSet(input.dataset.selectSet);
  }
  if (input.dataset.selectItem) {
    const setId = input.dataset.itemSet;
    resourcePicker.selection[setId] = toggleResourceItem(resourcePicker.selection[setId], resourcePicker.catalogs[setId].items, input.dataset.selectItem, input.checked);
    updatePickerSummary();
  }
});
document.addEventListener('keydown', event => {
  const chooser = event.target.closest('.resource-profile-picker');
  if (!chooser) return;
  const trigger = chooser.querySelector('summary');
  if (event.key === 'Escape') {
    chooser.open = false;
    trigger.focus();
    event.preventDefault();
    return;
  }
  if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
  const options = [...chooser.querySelectorAll('[data-resource-profile-choice]')];
  if (!options.length) return;
  event.preventDefault();
  chooser.open = true;
  const index = options.indexOf(document.activeElement);
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? options.length - 1 :
    index < 0 ? Math.max(0, options.findIndex(option => option.getAttribute('aria-pressed') === 'true')) :
    (index + (event.key === 'ArrowDown' ? 1 : -1) + options.length) % options.length;
  options[next].focus();
});
document.addEventListener('focusin', event => {
  const chooser = $('.resource-profile-picker');
  if (chooser && !chooser.contains(event.target)) chooser.open = false;
});
document.addEventListener('input', event => {
  if (event.target.dataset.itemQuery) {
    const query = event.target.value.trim().toLowerCase();
    const grid = $(`[data-picker-grid="${CSS.escape(event.target.dataset.itemQuery)}"]`);
    [...grid.children].forEach(item => { item.hidden = !item.dataset.itemSearch?.includes(query); });
  }
  if (event.target.id === 'shared-set-query') {
    const query = event.target.value.trim().toLowerCase();
    const cards = [...$('#shared-set-items').children]; let count = 0;
    cards.forEach((card, index) => {
      const item = state.openSet.items[index]; if (!item) return;
      const matches = [item.name, item.description, ...(item.tags || [])].join(' ').toLowerCase().includes(query);
      card.hidden = !matches; if (matches) count++;
    });
    $('#shared-set-count').textContent = `${count} resources`;
  }
});
$('#resource-picker-form').addEventListener('submit', async event => {
  event.preventDefault();
  const picker = resourcePicker;
  $('#resource-picker-save').disabled = true; $('#resource-picker-error').hidden = true;
  try {
    await api('/api/profile/update', { profile_id: picker.profile.id, revision: picker.profile.revision, values: selectedResourceValues(picker.selection, picker.sets) });
    $('#resources-dialog').close();
    await refreshOverview(); await loadDesign();
    if ($('#profile-dialog').open) await openReferencesWorkspace();
    toast('Resource selection saved');
  } catch (error) { $('#resource-picker-error').textContent = error.message; $('#resource-picker-error').hidden = false; }
  finally { $('#resource-picker-save').disabled = false; }
});
