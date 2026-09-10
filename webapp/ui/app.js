const state = { overview: null, view: "session", run: null, design: null, librarySets: null, openSet: null, system: null };
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const at = (value, key, fallback = null) => key.split(".").reduce((v, k) => v?.[k], value) ?? fallback;
const viewNames = { session: "Session", design: "Style", resources: "Resources", system: "System" };

async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Could not complete this action");
  return result;
}
let toastTimer;
function toast(message) { clearTimeout(toastTimer); $("#toast").textContent = message; $("#toast").hidden = false; toastTimer = setTimeout(() => { $("#toast").hidden = true; }, 4200); }
async function attempt(action) { try { await action(); } catch (error) { toast(error.message); } }
function empty(title, note) { return `<div class="empty-state"><strong>${esc(title)}</strong><p>${esc(note)}</p></div>`; }
function input(name, value, label, type = "text") { return `<label>${esc(label)}<input name="${esc(name)}" type="${type}" value="${esc(value)}"></label>`; }
function choiceCards(name, value, options, label, compact = false) {
  return `<fieldset><legend>${esc(label)}</legend><div class="choice-grid ${compact ? "compact" : ""}">${Object.entries(options).map(([key, option]) => { const [title, note] = Array.isArray(option) ? option : [option, ""]; return `<label class="choice-card"><input type="radio" name="${esc(name)}" value="${esc(key)}" ${String(value) === key ? "checked" : ""}><span><i aria-hidden="true"></i><strong>${esc(title)}</strong>${note ? `<small>${esc(note)}</small>` : ""}</span></label>`; }).join("")}</div></fieldset>`;
}

async function refreshOverview() {
  state.overview = await api("/api/context");
}
async function navigate(view) {
  view = view === "runs" || view === "overview" ? "session" : view;
  state.view = view;
  if (location.hash !== "#" + view) history.replaceState(null, "", location.pathname + location.search + "#" + view);
  $$('.view').forEach(panel => panel.classList.toggle("active", panel.id === "view-" + view));
  $$('.nav-item').forEach(button => button.classList.toggle("active", button.dataset.view === view));
  $("#panel-page-heading").hidden = view === "session";
  $("#view-title").textContent = viewNames[view];
  $("#view-eyebrow").textContent = "";
  $("#view-description").textContent = "";
  if (view === "session") await refreshPanel(true);
  if (view === "design") await loadStyleSurface();
  if (view === "resources") await loadResources();
  if (view === "system") await loadSystem();
}

function agencyLabel(value) { return ({ specified: "Defined", guided: "Flexible", agent_decides: "Open", agent_decides_from_references: "From references", agent_decides_within_profile: "Open" }[value] || "Flexible"); }
function styleCards(payload, session = false) {
  const v = payload.values;
  const agency = payload.style_agency || payload.config?.resolved_profile?.style_agency || {};
  const selectedSets = payload.selected_sets || payload.config?.library_sets?.selected || { icons: [], components: [] };
  const overrides = session ? state.run?.overrides || {} : {};
  const designOverrides = overrides.design_overrides || {};
  const styleOverrides = designOverrides.style || {};
  const changed = value => session ? `<span class="inheritance">${value ? "Changed for this presentation" : "Using the saved profile"}</span>` : "";
  const densityChanged = Boolean(overrides.density || styleOverrides.density);
  const typographyChanged = Boolean(styleOverrides.display_font || styleOverrides.body_font);
  const visualChanged = Boolean(styleOverrides.icon_treatment || styleOverrides.accent_colors || styleOverrides.background || designOverrides.semantic_style_tokens || designOverrides.title?.color);
  const librariesChanged = Boolean(overrides.library_sets);
  return `<button class="design-control" data-edit="guidance" data-session="${session}"><div class="design-copy"><span class="eyebrow">Information density</span><strong>${esc(payload.densities[v.density] || v.density)}</strong><p>From a few key ideas to a detailed analysis.</p>${changed(densityChanged)}<div class="density-summary"><span>${esc(agencyLabel(agency.density))}</span><span class="density-bars">${"<i></i>".repeat(v.density === "spacious" ? 2 : v.density === "information_rich" ? 6 : 4)}</span></div></div><div class="design-visual"><span class="communication-mini"><i></i><b></b><b></b><em></em></span><small>Configure</small></div></button>
  <button class="design-control" data-edit="typography" data-session="${session}"><div class="design-copy"><span class="eyebrow">Typography</span><strong>${esc(v.display_font)} <span class="type-divider">/</span> ${esc(v.body_font)}</strong><p>Headings and body text.</p>${changed(typographyChanged)}</div><div class="type-preview" data-display-font="${esc(v.display_font)}" data-body-font="${esc(v.body_font)}"><b>Aa</b><small>${esc(agencyLabel(agency.typography))}</small></div></button>
  <button class="design-control" data-edit="visual" data-session="${session}"><div class="design-copy"><span class="eyebrow">Color and treatment</span><strong>${esc(agencyLabel(agency.palette))} palette</strong><p>Choose colors or leave room to explore.</p>${changed(visualChanged)}</div><div class="palette-preview">${[v.primary, v.secondary, v.highlight, v.surface].map(color => `<i data-color="${esc(color)}"></i>`).join("")}<small>Configure</small></div></button>
  <button class="design-control" data-edit="libraries" data-session="${session}"><div class="design-copy"><span class="eyebrow">Icons and components</span><strong>${selectedSets.icons.length} icon · ${selectedSets.components.length} component set${selectedSets.components.length === 1 ? "" : "s"}</strong><p>Choose which sets are available to this style.</p>${changed(librariesChanged)}</div><div class="set-stack" aria-hidden="true"><span>◇</span><span>▦</span><small>Choose sets</small></div></button>`;
}
function applyPreviews() {
  $$('[data-edit="guidance"] .design-visual').forEach(element => {
    const session = element.closest('[data-session]').dataset.session === 'true';
    element.innerHTML = densityIllustration((session ? state.run : state.design).values.density) + '<small>Choose density</small>';
  });
  $$('[data-edit="visual"] .palette-preview').forEach(element => {
    element.querySelector('.treatment-illustration')?.remove();
    const session = element.closest('[data-session]').dataset.session === 'true';
    element.insertAdjacentHTML('beforeend', treatmentIllustration((session ? state.run : state.design).values.icon_treatment));
  });
  $$('[data-color]').forEach(element => { if (/^#[0-9a-f]{6}$/i.test(element.dataset.color)) element.style.backgroundColor = element.dataset.color; });
  $$('[data-display-font]').forEach(element => { element.querySelector("b").style.fontFamily = `${JSON.stringify(element.dataset.displayFont)}, serif`; element.querySelector("small").style.fontFamily = `${JSON.stringify(element.dataset.bodyFont)}, sans-serif`; });
  $$('[data-font]').forEach(element => { element.style.fontFamily = `${JSON.stringify(element.dataset.font)}, sans-serif`; });
}
function profilePreview(profile, values = {}) {
  const colors=profile.preview?.colors||[];
  const primary=values.primary||colors[0]||'#2f2f31', secondary=values.secondary||colors[1]||'#9a9a9f', surface=values.surface||colors[2]||'#f1f1f2';
  return `<span class="profile-mini adaptive" style="--preview-primary:${esc(primary)};--preview-secondary:${esc(secondary)};--preview-surface:${esc(surface)}"><i></i><b></b><em></em></span>`;
}
async function loadDesign() {
  state.design = await api("/api/design");
  const order = { "consulting": 0, "editorial-archive": 1, "monochrome-modern": 2 };
  const profiles = state.design.profiles.slice().sort((a, b) => (order[a.id] ?? 99) - (order[b.id] ?? 99));
  $("#profile-chooser").innerHTML = `<div class="profile-strip-heading"><div><p class="eyebrow">GUIDANCE PROFILES</p><h3>Your profiles</h3></div></div><div class="profile-strip">${profiles.map(profile => `<button class="profile-tile ${profile.id === state.design.values.profile ? "selected" : ""}" data-profile-choice="${esc(profile.id)}">${profilePreview(profile)}<span><strong>${esc(profile.name)}</strong><small>${esc(profile.purpose)}</small></span><i aria-hidden="true"></i></button>`).join("")}</div>`;
  $("#design-settings").innerHTML = styleCards(state.design) + '<button class="text-button" id="reset-default-style">Restore this profile’s original style</button>';
  await renderProfileContents();
  applyPreviews();
}

let saveEditor;
function editor(title, fields, save, options = {}) {
  $("#editor-title").textContent = title; $("#editor-scope").textContent = options.scope || "PRESENTATION DEFAULTS"; $("#editor-fields").innerHTML = fields; $("#editor-help").textContent = options.help ?? ""; $("#editor-error").hidden = true; $("#editor-save").textContent = options.label || "Save changes"; saveEditor = save; $("#editor-dialog").showModal(); applyPreviews();
}
function fontPicker(role, value, fonts) { return `<fieldset><legend>${role === "display_font" ? "Display typeface" : "Body typeface"}</legend><div class="font-grid">${[...new Set([value, ...fonts])].map(font => `<button type="button" class="font-choice ${value === font ? "selected" : ""}" data-font="${esc(font)}" data-font-role="${role}"><strong>${esc(font)}</strong><span>Ag 你好</span></button>`).join("")}</div>${input(role, value, "Typeface name")}</fieldset>`; }
async function openStyleEditor(mode, session) {
  const payload = session ? state.run : state.design; const v = payload.values;
  const agency = payload.style_agency || payload.config?.resolved_profile?.style_agency || {}; let fields = "";
  if (mode === "guidance") fields = choiceCards("density", v.density, { spacious: ["Spacious", "One clear idea with generous room"], balanced: ["Balanced", "A focused argument with supporting detail"], information_rich: ["Information-rich", "Detailed analysis with a clear reading order"] }, "Information density") + (!session ? choiceCards("density_mode", agency.density || "guided", { specified: "Keep this density", guided: "Allow some flexibility", agent_decides: "Choose for each presentation" }, "How flexible can it be?", true) : "");
  if (mode === "typography") fields = (!session ? choiceCards("typography_mode", agency.typography || "specified", { specified: "Use these typefaces", guided: "Use as a starting point", agent_decides: "Choose for each presentation" }, "Typography direction", true) : "") + fontPicker("display_font", v.display_font, payload.fonts) + fontPicker("body_font", v.body_font, payload.fonts);
  if (mode === "visual") fields = (!session ? choiceCards("palette_mode", agency.palette || "specified", { specified: ["Defined palette", "Use the values below"], guided: ["Flexible palette", "Keep its character while adapting"], agent_decides_from_references: ["From references", "Draw a coherent palette from the selected visuals"] }, "Color direction") : "") + `<fieldset><legend>Palette</legend><div class="color-grid">${Object.entries({ primary: "Primary", secondary: "Secondary", highlight: "Highlight", surface: "Soft surface", text: "Text", background: "Background" }).map(([key, name]) => `<label>${name}<div class="color-input"><input type="color" data-color-for="${key}" value="${esc(v[key])}"><input name="${key}" value="${esc(v[key])}" pattern="#[0-9a-fA-F]{6}"></div></label>`).join("")}</div></fieldset>` + choiceCards("icon_treatment", v.icon_treatment, { agent_decides: ["Choose for each presentation", "Match line, fill, and container to the composition"], plain: ["Plain", "No surrounding surface"], tinted_surface: ["Tinted surface", "Use a quiet supporting container"] }, "Icon treatment", true);
  if (mode === "libraries") {
    const selected = payload.selected_sets || payload.config?.library_sets?.selected || { icons: [], components: [] }; const sets = payload.library_sets || state.design.library_sets;
    fields = `<fieldset><legend>Icon Sets</legend><div class="set-choice-grid">${sets.filter(item => item.kind === "icons").map(item => `<label class="set-choice"><input type="checkbox" name="icon_sets" value="${esc(item.id)}" ${selected.icons.includes(item.id) ? "checked" : ""}><span><b>${item.source === "remote" ? "↗" : "◇"}</b><strong>${esc(item.name)}</strong><small>${esc(item.description)}</small></span></label>`).join("")}</div></fieldset><fieldset><legend>Component Sets</legend><div class="set-choice-grid">${sets.filter(item => item.kind === "components").map(item => `<label class="set-choice"><input type="checkbox" name="component_sets" value="${esc(item.id)}" ${selected.components.includes(item.id) ? "checked" : ""}><span><b>▦</b><strong>${esc(item.name)}</strong><small>${esc(item.description)}</small></span></label>`).join("")}</div></fieldset>`;
  }
  editor({ guidance: "Information density", typography: "Choose typefaces", visual: "Color and treatment", libraries: "Library Sets" }[mode], fields, async form => {
    const values = Object.fromEntries(form); const profileValues = {};
    if (!session && mode === "guidance") { profileValues.style_agency = { ...agency, density: values.density_mode }; delete values.density_mode; }
    if (!session && mode === "typography") { profileValues.style_agency = { ...agency, typography: values.typography_mode }; delete values.typography_mode; }
    if (!session && mode === "visual") { profileValues.style_agency = { ...agency, palette: values.palette_mode }; delete values.palette_mode; }
    const selectedLibrarySets = mode === "libraries" ? { icons: form.getAll("icon_sets"), components: form.getAll("component_sets") } : null;
    if (!session && selectedLibrarySets) { profileValues.library_sets = selectedLibrarySets; delete values.icon_sets; delete values.component_sets; }
    for (const key of Object.keys(values)) if (values[key] === v[key]) delete values[key];
    if (session) { if (selectedLibrarySets) state.run = await api("/api/override", { run: state.run.path, key: "library_sets", value: selectedLibrarySets, revision: state.run.overrides_revision }); else if (Object.keys(values).length) state.run = await api("/api/run/design", { run: state.run.path, values, revision: state.run.overrides_revision }); renderRun(); }
    else { if (Object.keys(profileValues).length) await api("/api/profile/update", { profile_id: v.profile, revision: payload.profile_revision, values: profileValues }); if (Object.keys(values).length) { const latest = await api(`/api/design?profile=${encodeURIComponent(v.profile)}`); await api("/api/design", { profile: v.profile, values, revision: latest.revision }); } await refreshOverview(); await loadDesign(); }
    toast(session ? "Applied to this presentation" : "Profile style saved");
  }, { scope: session ? "THIS PRESENTATION" : "GUIDANCE PROFILE", help: session ? "Your saved profile stays unchanged." : "", label: session ? "Apply" : "Save changes" });
}

async function renderRun() {
  if (state.view === "design") await loadStyleSurface();
  else await refreshPanel(true);
}

async function loadResources() {
  state.librarySets = await api("/api/library-sets");
  const groups = { icons: state.librarySets.sets.filter(item => item.kind === "icons"), components: state.librarySets.sets.filter(item => item.kind === "components") };
  $("#library-grid").innerHTML = Object.entries(groups).map(([kind, items]) => `<section class="library-group"><div class="library-group-heading"><span class="collection-symbol">${kind === "icons" ? iconGlyph() : "▦"}</span><div><h3>${kind === "icons" ? "Icon Sets" : "Component Sets"}</h3><p>${items.length} sets</p></div><button class="icon-button add-set-button" data-new-set="${kind}" aria-label="Add ${kind === "icons" ? "Icon" : "Component"} Set">＋</button></div><div class="set-list">${items.map(item => `<button class="set-row" data-library-set="${esc(item.id)}"><span class="set-source">${item.source === "remote" ? "Online" : "Local"}</span><span><strong>${esc(item.name)}</strong><small>${esc(item.description)}</small></span><b>›</b></button>`).join("")}</div></section>`).join("");
}
async function openLibrarySet(setId) {
  state.openSet = await api(`/api/library-set?set_id=${encodeURIComponent(setId)}`); const item = state.openSet;
  $("#library-title").textContent = item.name;
  $("#library-detail").innerHTML = `<div class="collection-intro"><p>${esc(item.description)}</p><div class="inline-actions"><button class="text-button" data-edit-set>Set details</button>${item.source === "local" ? '<button class="quiet-button" id="add-set-resource">＋ Add to set</button>' : ""}</div></div>${item.source === "remote" ? remoteSetContents(item) : `<div class="library-item-grid">${item.items.map(asset => item.kind === "components" ? `<button class="resource-card native-tile" data-component="${esc(asset.id)}"><div class="native-mini">${componentSymbol(asset)}</div><div class="resource-copy"><span class="eyebrow">${asset.path?.endsWith(".pptx") ? "EDITABLE POWERPOINT" : "DESIGN GRAMMAR"}</span><h4>${esc(asset.name || asset.id)}</h4><p>${esc(asset.description || "")}</p><span class="text-link">Inspect component</span></div></button>` : `<article class="resource-card"><button class="resource-thumbnail" data-preview="${esc(asset.asset_url || "")}" data-title="${esc(asset.name || asset.id)}"><img src="${esc(asset.asset_url || "")}" alt="${esc(asset.name || asset.id)}"></button><div class="resource-copy"><h4>${esc(asset.name || asset.id)}</h4><p>${esc(asset.description || "")}</p></div></article>`).join("")}</div>`}`;
  if (!$("#library-dialog").open) $("#library-dialog").showModal();
}
async function loadSystem() {
  state.system = await api("/api/settings");
  const health = await api("/api/health");
  $("#system-settings").innerHTML = "";
  $("#health-grid").innerHTML = health.map(item => `<article class="health-card"><span class="status-label ${item.available ? "" : "unavailable"}">${item.available ? "Ready" : "Not installed"}</span><h4>${esc(item.name)}</h4><p>${esc(item.detail)}</p></article>`).join("");
}
async function fileData(file) { const bytes = new Uint8Array(await file.arrayBuffer()); let binary = ""; for (let offset = 0; offset < bytes.length; offset += 8192) binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192)); return btoa(binary); }

document.addEventListener("click", event => attempt(async () => {
  const button = event.target.closest("button"); if (!button) return;
  if (button.hasAttribute("data-close")) return button.closest("dialog").close();
  if (button.dataset.view) return navigate(button.dataset.view);
  
  if (button.dataset.profileChoice) { await api("/api/profile", { profile_id: button.dataset.profileChoice }); await refreshOverview(); await loadDesign(); return toast("Profile selected"); }
  if (button.dataset.edit) return openStyleEditor(button.dataset.edit, button.dataset.session === "true");
  if (button.dataset.fontRole) { const role = button.dataset.fontRole; $(`#editor-fields input[name="${role}"]`).value = button.dataset.font; $$(`[data-font-role="${role}"]`).forEach(element => element.classList.toggle("selected", element === button)); return; }
  if (button.hasAttribute("data-preview")) { if (!button.dataset.preview) return; $("#preview-body").classList.remove("zoomed"); $("#zoom-preview").textContent = "Zoom in"; $("#preview-title").textContent = button.dataset.title; $("#preview-body").innerHTML = `<img src="${esc(button.dataset.preview)}" alt="${esc(button.dataset.title)}">`; return $("#preview-dialog").showModal(); }
  if (button.dataset.librarySet) return openLibrarySet(button.dataset.librarySet);
  
  if (button.id === "add-set-resource") return editor("Add to Library Set", '<label>File<input type="file" name="file" required></label>' + input("name", "", "Name") + '<label>Description<textarea name="description" rows="3"></textarea></label>' + input("tags", "", "Tags · comma separated") + input("source_url", "", "Source URL") + input("license", "", "License / usage permission"), async form => { const values = Object.fromEntries(form); const file = values.file; delete values.file; values.tags = values.tags.split(",").map(tag => tag.trim()).filter(Boolean); await api("/api/library-set/add", { ...values, set_id: state.openSet.id, filename: file.name, content_base64: await fileData(file) }); await openLibrarySet(state.openSet.id); toast("Resource added to the set"); }, { scope: state.openSet.name.toUpperCase(), help: "Icons require license information. Components keep their source and descriptive metadata.", label: "Add resource" });
  if (button.id === "new-profile") return editor("Create a guidance profile", input("name", "", "Profile name") + choiceCards("based_on", state.design.values.profile, Object.fromEntries(state.overview.profiles.map(profile => [profile.id, [profile.name, profile.purpose]])), "Starting point") + '<label>What should this style express?<textarea name="purpose" rows="4"></textarea></label>', async form => { const result = await api("/api/profile/create", Object.fromEntries(form)); await refreshOverview(); await loadDesign(); toast(`${result.profile.name} created`); }, { scope: "GUIDANCE PROFILE", help: "Start with the closest look and adjust it anytime.", label: "Create profile" });
  if (button.id === "edit-profile") return openProfileWorkspace();
  
  if (button.id === "reset-default-style") return editor("Restore profile style?", "<p>Restore this profile’s original fonts, colors, and density. Existing presentations stay the same.</p>", async () => { await api("/api/design", { profile: state.design.values.profile, reset: true, revision: state.design.revision }); await loadDesign(); toast("Profile style restored"); }, { label: "Restore style" });
  if (button.id === "reset-run-style") return editor("Use the saved profile?", "<p>Remove the font, palette, and density changes made for this presentation.</p>", async () => { state.run = await api("/api/run/design", { run: state.run.path, reset: true, revision: state.run.overrides_revision }); renderRun(); toast("Saved profile restored"); }, { scope: "THIS PRESENTATION", label: "Use saved profile" });
  if (button.id === "refresh-run-defaults") return editor("Update from the profile?", "<p>Bring in the latest profile and Library Sets. Changes made for this presentation will stay in place.</p>", async () => { state.run = await api("/api/run/defaults", { run: state.run.path, revision: state.run.defaults_revision }); renderRun(); toast("Profile updated"); }, { scope: "THIS PRESENTATION", label: "Update" });
}));

document.addEventListener("input", event => { if (event.target.dataset.colorFor) $(`#editor-fields input[name="${event.target.dataset.colorFor}"]`).value = event.target.value; });
$("#editor-form").addEventListener("submit", async event => { event.preventDefault(); $("#editor-save").disabled = true; $("#editor-error").hidden = true; try { await saveEditor(new FormData(event.currentTarget)); $("#editor-dialog").close(); } catch (error) { $("#editor-error").textContent = error.message; $("#editor-error").hidden = false; } finally { $("#editor-save").disabled = false; } });
