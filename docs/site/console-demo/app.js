const state = { consoleProfile: null, overview: null, view: "overview", design: null, librarySets: null, openSet: null, system: null };
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const at = (value, key, fallback = null) => key.split(".").reduce((v, k) => v?.[k], value) ?? fallback;
const viewNames = { overview: "Overview", design: "Style", resources: "Resources", system: "System" };
const capabilityInfo = {
  Python: { key: "python", card: "Local tools", mark: "Py", purpose: "Prepares files and runs the tools used to build your presentation.", example: "Prepare a slide for measurement and reconstruction." },
  OpenCV: { key: "opencv", card: "Visual measurement", mark: "CV", purpose: "Measures positions, colors, edges, and connectors in the approved design.", example: "Match editable objects to the design you approved." },
  Node: { key: "node", card: "PowerPoint builder", mark: "JS", purpose: "Builds the editable PowerPoint file on this computer.", example: "Reconstruct an approved design as a PowerPoint slide." },
  PptxGenJS: { key: "pptx", card: "Editable objects", mark: "P", purpose: "Creates editable text, shapes, images, tables, and connectors.", example: "Keep supported slide elements editable in PowerPoint." },
  LibreOffice: { key: "libreoffice", card: "Slide previews", mark: "Pg", purpose: "Renders PowerPoint previews on this computer.", example: "Review the reconstructed slide before downloading it." },
  Poppler: { key: "poppler", card: "Preview images", mark: "PDF", purpose: "Converts LibreOffice PDF pages into images for visual review.", example: "Inspect each rendered slide with its text, charts and images." },
};

async function api(path, body) { return window.consoleDemoAPI(path, body); }

let toastTimer;
function toast(message) { clearTimeout(toastTimer); $("#toast").textContent = message; $("#toast").hidden = false; toastTimer = setTimeout(() => { $("#toast").hidden = true; }, 4200); }
async function attempt(action) { try { await action(); } catch (error) { toast(error.message); } }
function empty(title, note) { return `<div class="empty-state"><strong>${esc(title)}</strong><p>${esc(note)}</p></div>`; }
function input(name, value, label, type = "text") { return `<label>${esc(label)}<input name="${esc(name)}" type="${type}" value="${esc(value)}"></label>`; }
function choiceCards(name, value, options, label, compact = false) {
  return `<fieldset><legend>${esc(label)}</legend><div class="choice-grid ${compact ? "compact" : ""}">${Object.entries(options).map(([key, option]) => { const [title, note] = Array.isArray(option) ? option : [option, ""]; return `<label class="choice-card"><input type="radio" name="${esc(name)}" value="${esc(key)}" ${String(value) === key ? "checked" : ""}><span><i aria-hidden="true"></i><strong>${esc(title)}</strong>${note ? `<small>${esc(note)}</small>` : ""}</span></label>`; }).join("")}</div></fieldset>`;
}

async function refreshOverview() {
  state.overview = await api("/api/overview");
  const profile = state.overview.profiles.find(p => p.id === state.overview.active_profile);
  $("#metrics").innerHTML = `<article class="metric-card"><span>Guidance profiles</span><strong>${state.overview.profiles.length}</strong><small>Reusable visual systems</small></article><article class="metric-card"><span>Default style</span><strong class="metric-profile">${esc(profile?.name)}</strong><button class="text-button" data-view="design">Change</button></article>`;
}
async function navigate(view, focusHeading = false) {
  state.view = view;
  if (location.hash !== `#${view}`) history.replaceState(null, "", `#${view}`);
  $$('.view').forEach(panel => panel.classList.toggle("active", panel.id === `view-${view}`));
  $$('.nav-item').forEach(button => { button.classList.toggle("active", button.dataset.view === view); button.setAttribute('aria-label', viewNames[button.dataset.view]); if (button.dataset.view === view) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current'); });
  $("#view-title").textContent = viewNames[view];
  $("#view-eyebrow").textContent = view === "design" ? "PRESENTATION DESIGN" : "WORKSPACE";
  const description = {
    overview: "Your reusable styles, resources, and local capabilities.",
    design: "Create and customize your presentation styles.",
    resources: "Icons and editable components for your slides.",
    system: "Sample tool status. Your computer is not inspected."
  }[view];
  $("#view-description").textContent = description;
  $("#view-description").hidden = !description;
  if (focusHeading) $("#view-title").focus({ preventScroll: true });
  window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  if (view === "design") await loadDesign();
  if (view === "resources") await loadResources();
  if (view === "system") await loadSystem();
}

function agencyLabel(value) { return ({ specified: "Defined", guided: "Flexible", agent_decides: "Open", agent_decides_from_references: "From references", agent_decides_within_profile: "Open" }[value] || "Flexible"); }
function styleCards(payload) {
  const v = payload.values;
  const agency = payload.style_agency || payload.config?.resolved_profile?.style_agency || {};
  const selectedSets = payload.selected_sets || payload.config?.library_sets?.selected || { icons: [], components: [] };
  return `<button class="design-control" data-edit="guidance"><div class="design-copy"><span class="eyebrow">Information density</span><strong>${esc(payload.densities[v.density] || v.density)}</strong><p>Choose how much information your slides usually carry.</p><div class="density-summary"><span>${esc(agencyLabel(agency.density))}</span><span class="density-bars">${"<i></i>".repeat(v.density === "spacious" ? 2 : v.density === "information_rich" ? 6 : 4)}</span></div></div><div class="design-visual"><span class="communication-mini"><i></i><b></b><b></b><em></em></span><small>Choose</small></div></button>
  <button class="design-control" data-edit="typography"><div class="design-copy"><span class="eyebrow">Typography</span><strong>${esc(v.display_font)} <span class="type-divider">/</span> ${esc(v.body_font)}</strong><p>Choose typefaces for headings and body text.</p></div><div class="type-preview" data-display-font="${esc(v.display_font)}" data-body-font="${esc(v.body_font)}"><b>Aa</b><small>${esc(agencyLabel(agency.typography))}</small></div></button>
  <button class="design-control" data-edit="visual"><div class="design-copy"><span class="eyebrow">Color and treatment</span><strong>${esc(agencyLabel(agency.palette))} palette</strong><p>Set a palette or draw colors from your visual references.</p><div class="palette-preview">${[v.primary, v.secondary, v.highlight, v.surface].map(color => `<i data-color="${esc(color)}"></i>`).join("")}<small>Choose</small></div></button>
  <button class="design-control" data-edit="libraries"><div class="design-copy"><span class="eyebrow">Reusable elements</span><strong>${selectedSets.icons.length} icon · ${selectedSets.components.length} component set${selectedSets.components.length === 1 ? "" : "s"}</strong><p>Choose the icon and component sets available to this profile.</p></div><div class="set-stack" aria-hidden="true"><span>◇</span><span>▦</span><small>Choose sets</small></div></button>`;
}
function applyPreviews() {
  $$('[data-edit="guidance"] .design-visual').forEach(element => {
    element.innerHTML = densityIllustration(state.design.values.density) + '<small>Choose density</small>';
  });
  $$('[data-edit="visual"] .palette-preview').forEach(element => {
    element.querySelector('.treatment-illustration')?.remove();
    element.insertAdjacentHTML('beforeend', treatmentIllustration(state.design.values.icon_treatment));
  });
  $$('[data-color]').forEach(element => { if (/^#[0-9a-f]{6}$/i.test(element.dataset.color)) element.style.backgroundColor = element.dataset.color; });
  $$('[data-display-font]').forEach(element => { element.querySelector("b").style.fontFamily = `${JSON.stringify(element.dataset.displayFont)}, serif`; element.querySelector("small").style.fontFamily = `${JSON.stringify(element.dataset.bodyFont)}, sans-serif`; });
  $$('[data-font]').forEach(element => { element.style.fontFamily = `${JSON.stringify(element.dataset.font)}, sans-serif`; });
}
function profilePreview(profile) { const colors = profile.preview?.colors || []; return `<span class="profile-mini adaptive" style="--preview-primary:${esc(colors[0] || '#2f2f31')};--preview-secondary:${esc(colors[1] || '#9a9a9f')};--preview-surface:${esc(colors[2] || '#f1f1f2')}"><i></i><b></b><em></em></span>`; }
let designRequest = 0;
async function loadDesign() {
  const request = ++designRequest;
  const design = await api('/api/design' + (state.consoleProfile ? '?profile=' + encodeURIComponent(state.consoleProfile) : ''));
  if (request !== designRequest) return;
  state.design = design;
  state.overview.active_profile = design.active_profile;
  state.overview.profiles = design.profiles;
  const order = { 'consulting': 0, 'personal-website': 1, 'personal-monochrome': 2 };
  const profiles = state.design.profiles.slice().sort((a, b) => (order[a.id] ?? 99) - (order[b.id] ?? 99));
  if (!state.consoleProfile) {
    $('#profile-chooser').innerHTML = '<div class="profile-list-actions"><button class="quiet-button" id="new-profile">＋ Add profile</button></div><div class="profile-strip">' + profiles.map(profile => { const selected = state.overview.active_profile === profile.id; return '<article class="profile-tile ' + (selected ? 'selected' : '') + '"><button class="profile-open" data-profile-open="' + esc(profile.id) + '">' + profilePreview(profile) + '<span><strong>' + esc(profile.name) + '</strong><small>' + esc(profile.purpose) + '</small></span><b aria-hidden="true">›</b></button><button class="profile-default-control ' + (selected ? 'selected' : '') + '" data-profile-default="' + esc(profile.id) + '" aria-pressed="' + selected + '" ' + (selected ? 'disabled' : '') + '><i aria-hidden="true"></i>' + (selected ? 'Default' : 'Use as default') + '</button></article>'; }).join('') + '</div>';
    $('#design-settings').innerHTML = '';
    $('#profile-contents')?.remove();
    $$('[data-profile-default]').forEach(button => {
      const profile = profiles.find(item => item.id === button.dataset.profileDefault);
      button.setAttribute('aria-label', button.disabled ? `${profile.name}, default profile` : `Use ${profile.name} as default`);
    });
    return;
  }
  const profile = profiles.find(item => item.id === state.consoleProfile);
  $('#profile-chooser').innerHTML = '<div class="profile-workspace-heading"><button class="text-button" id="all-profiles">‹ All profiles</button><div><p class="eyebrow">GUIDANCE PROFILE</p><h2>' + esc(profile.name) + '</h2><p>' + esc(profile.purpose) + '</p></div></div>';
  $('#design-settings').innerHTML = styleCards(state.design) + '<button class="text-button" id="reset-default-style">Restore original style</button>';
  await renderProfileContents();
  applyPreviews();
}

async function selectDefaultProfile(profileId) {
  if (state.defaultSaving || state.overview.active_profile === profileId) return;
  state.defaultSaving = true;
  const controls = $$('[data-profile-default]');
  controls.forEach(button => { button.disabled = true; if (button.dataset.profileDefault === profileId) { button.textContent = 'Applying…'; button.setAttribute('aria-busy', 'true'); } });
  try {
    await api('/api/profile', { profile_id: profileId });
    await refreshOverview();
    if (state.view === 'design') await loadDesign();
    toast('Default profile updated');
  } finally {
    state.defaultSaving = false;
    controls.forEach(button => { button.disabled = button.dataset.profileDefault === state.overview.active_profile; button.removeAttribute('aria-busy'); button.innerHTML = '<i aria-hidden="true"></i>' + (button.disabled ? 'Default' : 'Use as default'); });
  }
}


let saveEditor;
function editor(title, fields, save, options = {}) {
  $("#editor-title").textContent = title; $("#editor-scope").textContent = options.scope || "PRESENTATION DEFAULTS"; $("#editor-fields").innerHTML = fields; $("#editor-help").textContent = options.help ?? ""; $("#editor-error").hidden = true; $("#editor-save").textContent = options.label || "Save changes"; saveEditor = save; $("#editor-dialog").showModal(); applyPreviews();
}
function fontPicker(role, value, fonts) { return `<fieldset><legend>${role === "display_font" ? "Display typeface" : "Body typeface"}</legend><div class="font-grid">${[...new Set([value, ...fonts])].map(font => `<button type="button" class="font-choice ${value === font ? "selected" : ""}" data-font="${esc(font)}" data-font-role="${role}"><strong>${esc(font)}</strong><span>Ag 你好</span></button>`).join("")}</div>${input(role, value, "Typeface name")}</fieldset>`; }
async function openStyleEditor(mode) {
  const payload = state.design; const v = payload.values;
  const agency = payload.style_agency || payload.config?.resolved_profile?.style_agency || {}; let fields = "";
  if (mode === "guidance") fields = choiceCards("density", v.density, { spacious: ["Spacious", "One clear idea with generous room"], balanced: ["Balanced", "A focused argument with supporting detail"], information_rich: ["Information-rich", "Detailed analysis with a clear reading order"] }, "Information density") + choiceCards("density_mode", agency.density || "guided", { specified: "Keep this density", guided: "Allow some flexibility", agent_decides: "Choose for each presentation" }, "How flexible can it be?", true);
  if (mode === "typography") fields = choiceCards("typography_mode", agency.typography || "specified", { specified: "Use these typefaces", guided: "Use as a starting point", agent_decides: "Choose for each presentation" }, "Typography direction", true) + fontPicker("display_font", v.display_font, payload.fonts) + fontPicker("body_font", v.body_font, payload.fonts);
  if (mode === "visual") fields = choiceCards("palette_mode", agency.palette || "specified", { specified: ["Defined palette", "Use the values below"], guided: ["Flexible palette", "Keep its character while adapting"], agent_decides_from_references: ["From references", "Draw a coherent palette from the selected visuals"] }, "Color direction") + `<fieldset><legend>Palette</legend><div class="color-grid">${Object.entries({ primary: "Primary", secondary: "Secondary", highlight: "Highlight", surface: "Soft surface", text: "Text", background: "Background" }).map(([key, name]) => `<label>${name}<div class="color-input"><input type="color" data-color-for="${key}" value="${esc(v[key])}"><input name="${key}" value="${esc(v[key])}" pattern="#[0-9a-fA-F]{6}"></div></label>`).join("")}</div></fieldset>` + choiceCards("icon_treatment", v.icon_treatment, { agent_decides: ["Choose for each presentation", "Match line, fill, and container to the composition"], plain: ["Plain", "No surrounding surface"], tinted_surface: ["Tinted surface", "Use a quiet supporting container"] }, "Icon treatment", true);
  if (mode === "libraries") {
    const selected = payload.selected_sets || payload.config?.library_sets?.selected || { icons: [], components: [] }; const sets = payload.library_sets || state.design.library_sets;
    fields = `<fieldset><legend>Icon Sets</legend><div class="set-choice-grid">${sets.filter(item => item.kind === "icons").map(item => `<label class="set-choice"><input type="checkbox" name="icon_sets" value="${esc(item.id)}" ${selected.icons.includes(item.id) ? "checked" : ""}><span><b>${item.source === "remote" ? "↗" : "◇"}</b><strong>${esc(item.name)}</strong><small>${esc(item.description)}</small></span></label>`).join("")}</div></fieldset><fieldset><legend>Component Sets</legend><div class="set-choice-grid">${sets.filter(item => item.kind === "components").map(item => `<label class="set-choice"><input type="checkbox" name="component_sets" value="${esc(item.id)}" ${selected.components.includes(item.id) ? "checked" : ""}><span><b>▦</b><strong>${esc(item.name)}</strong><small>${esc(item.description)}</small></span></label>`).join("")}</div></fieldset>`;
  }
  editor({ guidance: "Information density", typography: "Choose typefaces", visual: "Color and treatment", libraries: "Library Sets" }[mode], fields, async form => {
    const values = Object.fromEntries(form); const profileValues = {};
    if (mode === "guidance") { profileValues.style_agency = { density: values.density_mode }; delete values.density_mode; }
    if (mode === "typography") { profileValues.style_agency = { typography: values.typography_mode }; delete values.typography_mode; }
    if (mode === "visual") { profileValues.style_agency = { palette: values.palette_mode }; delete values.palette_mode; }
    const selectedLibrarySets = mode === "libraries" ? { icons: form.getAll("icon_sets"), components: form.getAll("component_sets") } : null;
    if (selectedLibrarySets) { profileValues.library_sets = selectedLibrarySets; delete values.icon_sets; delete values.component_sets; }
    for (const key of Object.keys(values)) if (values[key] === v[key]) delete values[key];
    if (Object.keys(profileValues).length || Object.keys(values).length) await api("/api/profile/style", { profile: v.profile, values, profile_values: profileValues, revision: payload.revision, profile_revision: payload.profile_revision });
    await refreshOverview(); await loadDesign();
    toast("Profile style saved");
  }, { scope: "GUIDANCE PROFILE", help: "These choices guide future presentations." });
}

async function loadResources() {
  state.librarySets = await api("/api/library-sets");
  const groups = { icons: state.librarySets.sets.filter(item => item.kind === "icons"), components: state.librarySets.sets.filter(item => item.kind === "components") };
  $("#library-grid").innerHTML = Object.entries(groups).map(([kind, items]) => `<section class="library-group"><div class="library-group-heading"><span class="collection-symbol">${kind === "icons" ? iconGlyph() : "▦"}</span><div><p class="eyebrow">${kind === "icons" ? "ICONS" : "COMPONENTS"}</p><h3>${kind === "icons" ? "Icon Sets" : "Component Sets"}</h3><p>${items.length} sets</p></div><button class="icon-button add-set-button" data-new-set="${kind}" aria-label="Add ${kind === "icons" ? "Icon" : "Component"} Set">＋</button></div><div class="set-list">${items.map(item => `<button class="set-row" data-library-set="${esc(item.id)}"><span class="set-source">${item.source === "remote" ? "Online" : "Local"}</span><span><strong>${esc(item.name)}</strong><small>${esc(item.description)}</small></span><b>›</b></button>`).join("")}</div></section>`).join("");
}
async function openLibrarySet(setId) {
  state.openSet = await api(`/api/library-set?set_id=${encodeURIComponent(setId)}`); const item = state.openSet;
  $("#library-title").textContent = item.name;
  $("#library-detail").innerHTML = `<div class="collection-intro"><p>${esc(item.description)}</p><div class="inline-actions"><button class="text-button" data-edit-set>Set details</button>${item.source === "local" ? '<button class="quiet-button" id="add-set-resource">＋ Add to set</button>' : ""}</div></div>${item.source === "remote" ? remoteSetContents(item) : `<div class="library-item-grid">${item.items.map(asset => item.kind === "components" ? `<button class="resource-card native-tile" data-component="${esc(asset.id)}"><div class="native-mini">${componentSymbol(asset)}</div><div class="resource-copy"><span class="eyebrow">${asset.path?.endsWith(".pptx") ? "EDITABLE POWERPOINT" : "DESIGN GRAMMAR"}</span><h4>${esc(asset.name || asset.id)}</h4><p>${esc(asset.description || "")}</p><span class="text-link">Inspect component</span></div></button>` : `<article class="resource-card"><button class="resource-thumbnail" data-preview="${esc(asset.asset_url || "")}" data-title="${esc(asset.name || asset.id)}"><img src="${esc(asset.asset_url || "")}" alt="${esc(asset.name || asset.id)}"></button><div class="resource-copy"><h4>${esc(asset.name || asset.id)}</h4><p>${esc(asset.description || "")}</p></div></article>`).join("")}</div>`}`;
  if (!$("#library-dialog").open) $("#library-dialog").showModal();
}
async function loadSystem() {
  state.system = await api("/api/settings");
  const health = await api("/api/health"); state.health = health;
  $("#system-settings").innerHTML = "";
  renderHealth();
}
function renderHealth() {
  $("#health-grid").innerHTML = state.health.map(item => { const info = capabilityInfo[item.name]; return `<button class="health-card" data-capability="${esc(item.name)}"><span class="status-label ${item.available ? "" : "unavailable"}">${item.available ? "Ready" : "Not installed"}</span><h4>${esc(item.name)}</h4><p>${esc(info?.card || item.detail)}</p><b aria-hidden="true">›</b></button>`; }).join("");
}
function openCapability(name) {
  const item = state.health.find(entry => entry.name === name); const info = capabilityInfo[name]; if (!item || !info) return;
  $("#preview-title").textContent = item.name;
  $("#preview-body").innerHTML = `<div class="capability-detail"><div class="capability-sample ${esc(info.key)}" aria-hidden="true"><strong>${esc(info.mark)}</strong><span><i></i><i></i><i></i></span></div><div class="capability-copy"><p class="capability-lead">${esc(info.purpose)}</p><dl><div><dt>Example</dt><dd>${esc(info.example)}</dd></div><div><dt>Status</dt><dd>${item.available ? "Ready on this computer" : "Not installed"}</dd></div><div><dt>Installation details</dt><dd>${esc(item.detail)}</dd></div></dl></div></div>`;
  if (!$("#preview-dialog").open) $("#preview-dialog").showModal();
}
async function fileData(file) { const bytes = new Uint8Array(await file.arrayBuffer()); let binary = ""; for (let offset = 0; offset < bytes.length; offset += 8192) binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192)); return btoa(binary); }

document.addEventListener("click", event => attempt(async () => {
  const button = event.target.closest("button"); if (!button) return;
  if (button.hasAttribute("data-close")) return button.closest("dialog").close();
  if (button.dataset.view) return navigate(button.dataset.view, true);
  if (button.dataset.profileDefault) return selectDefaultProfile(button.dataset.profileDefault);
  if (button.dataset.profileOpen) { state.consoleProfile = button.dataset.profileOpen; return loadDesign(); }
  if (button.id === 'all-profiles') { state.consoleProfile = null; return loadDesign(); }
  if (button.dataset.edit) return openStyleEditor(button.dataset.edit);
  if (button.dataset.fontRole) { const role = button.dataset.fontRole; $(`#editor-fields input[name="${role}"]`).value = button.dataset.font; $$(`[data-font-role="${role}"]`).forEach(element => element.classList.toggle("selected", element === button)); return; }
  if (button.hasAttribute("data-preview")) { if (!button.dataset.preview) return; $("#preview-title").textContent = button.dataset.title; $("#preview-body").innerHTML = `<img src="${esc(button.dataset.preview)}" alt="${esc(button.dataset.title)}">`; return $("#preview-dialog").showModal(); }
  if (button.dataset.librarySet) return openLibrarySet(button.dataset.librarySet);
  if (button.dataset.capability) return openCapability(button.dataset.capability);
  if (button.id === "close-library-set") { state.openSet = null; $("#library-detail").hidden = true; return; }
  if (button.id === "new-library-set") return editor("Create a Library Set", choiceCards("kind", "icons", { icons: ["Icon Set", "A coherent symbol family"], components: ["Component Set", "Reusable editable structures"] }, "Set type") + input("name", "", "Set name") + '<label>Description<textarea name="description" rows="3"></textarea></label>', async form => { const created = await api("/api/library-set/create", Object.fromEntries(form)); await loadResources(); await openLibrarySet(created.id); toast("Library Set created"); }, { scope: "RESOURCE LIBRARY", help: "Profiles can share a set without duplicating its assets.", label: "Create set" });
  if (button.id === "add-set-resource") return editor("Add to Library Set", '<label>File<input type="file" name="file" required></label>' + input("name", "", "Name") + '<label>Description<textarea name="description" rows="3"></textarea></label>' + input("tags", "", "Tags · comma separated") + input("source_url", "", "Source URL") + input("license", "", "License / usage permission"), async form => { const values = Object.fromEntries(form); const file = values.file; delete values.file; values.tags = values.tags.split(",").map(tag => tag.trim()).filter(Boolean); await api("/api/library-set/add", { ...values, set_id: state.openSet.id, filename: file.name, content_base64: await fileData(file) }); await openLibrarySet(state.openSet.id); toast("Resource added to the set"); }, { scope: state.openSet.name.toUpperCase(), help: "Icons require license information. Components keep their source and descriptive metadata.", label: "Add resource" });
  if (button.id === "new-profile") return editor("Create a guidance profile", input("name", "", "Profile name") + choiceCards("based_on", state.design.values.profile, Object.fromEntries(state.overview.profiles.map(profile => [profile.id, [profile.name, profile.purpose]])), "Starting point") + '<label>What should this style express?<textarea name="purpose" rows="4"></textarea></label>', async form => { const result = await api("/api/profile/create", Object.fromEntries(form)); await refreshOverview(); await loadDesign(); toast(`${result.profile.name} created`); }, { scope: "GUIDANCE PROFILE", help: "Start with the closest look and adjust it anytime.", label: "Create profile" });
  if (button.id === "reset-default-style") return editor("Restore profile style?", "<p>Restore this profile’s original fonts, colors, and density. Existing presentations stay the same.</p>", async () => { await api("/api/design", { profile: state.design.values.profile, reset: true, revision: state.design.revision }); await loadDesign(); toast("Profile style restored"); }, { label: "Restore style" });
}));

document.addEventListener("input", event => { if (event.target.dataset.colorFor) $(`#editor-fields input[name="${event.target.dataset.colorFor}"]`).value = event.target.value; });
$("#editor-form").addEventListener("submit", async event => { event.preventDefault(); $("#editor-save").disabled = true; $("#editor-error").hidden = true; try { await saveEditor(new FormData(event.currentTarget)); $("#editor-dialog").close(); } catch (error) { $("#editor-error").textContent = error.message; $("#editor-error").hidden = false; } finally { $("#editor-save").disabled = false; } });
$$('dialog').forEach(dialog => { const title = dialog.querySelector('h2[id]'); if (title) dialog.setAttribute('aria-labelledby', title.id); });
let sharedRevision, sharedPoll;
async function refreshSharedFiles() {
  if (document.hidden || $('dialog[open]') || document.activeElement?.matches('input,textarea,select') || state.defaultSaving) return;
  const latest = await api('/api/console/revision');
  if (latest.revision === sharedRevision) return;
  const view = state.view;
  await refreshOverview();
  if (state.view !== view) return;
  if (view === 'design') {
    if (!state.overview.profiles.some(p => p.id === state.consoleProfile)) state.consoleProfile = null;
    await loadDesign();
  }
  if (view === 'resources') await loadResources();
  if (view === 'system') await loadSystem();
  sharedRevision = latest.revision;
}
function scheduleSharedRefresh() {
  clearTimeout(sharedPoll);
  sharedPoll = setTimeout(async () => {
    try { await refreshSharedFiles(); } catch (_) { /* Retry without discarding the last readable view. */ }
    finally { scheduleSharedRefresh(); }
  }, 1800);
}
attempt(async () => { await refreshOverview(); const requested = location.hash.slice(1); await navigate(viewNames[requested] ? requested : "overview"); scheduleSharedRefresh(); });
