let panelPoll, sessionSnapshot;

async function bootPanel() {
  await refreshOverview();
  const query = new URLSearchParams(location.search);
  const panelId = query.get("panel");
  const legacyRun = query.get("run");
  if (panelId) state.panelBinding = await api(`/api/panel/binding?id=${encodeURIComponent(panelId)}`);
  const selected = state.panelBinding?.run || legacyRun;
  if (selected) {
    try { state.run = await api(`/api/run?path=${encodeURIComponent(selected)}`); }
    catch (error) { state.missingRun = error.message; }
  }
  await refreshPanel(true);
  schedulePanelPoll();
}

function schedulePanelPoll() {
  clearTimeout(panelPoll);
  panelPoll = setTimeout(async () => {
    try {
      if (!document.hidden) {
        if (state.panelBinding) {
          const binding = await api(`/api/panel/binding?id=${encodeURIComponent(state.panelBinding.id)}`);
          if (binding.run && binding.run !== state.run?.path) {
            state.panelBinding = binding;
            state.run = await api(`/api/run?path=${encodeURIComponent(binding.run)}`);
          }
        }
        await refreshPanel();
      }
    } catch (_) { /* Keep the last readable settings and retry quietly. */ }
    finally { schedulePanelPoll(); }
  }, 1800);
}

function assetsContent() {
  const materials = sessionSnapshot?.materials || [];
  return `<section class="session-section"><div class="section-title"><h2>Presentation assets</h2><label class="asset-add">＋ Add<input id="session-assets" type="file" multiple></label></div>${materials.length ? `<div class="asset-list">${materials.map(file => `<a href="${esc(file.url)}" target="_blank"><strong>${esc(file.name)}</strong><small>${Math.ceil(file.size / 1024)} KB</small></a>`).join("")}</div>` : '<p class="stage-empty">Add images, logos, or source files for this presentation.</p>'}</section>`;
}

function pendingChanges() {
  const count = sessionSnapshot?.pending_events?.events?.length || 0;
  if (!count) return "";
  return `<div class="panel-change"><span></span><div><strong>${count} ${count === 1 ? "change" : "changes"} saved</strong><small>They will be used before the next affected operation.</small></div></div>`;
}

function styleContent() {
  const profile = state.run.resolved_config.resolved_profile;
  return `<section class="style-foundation"><div class="profile-inheritance">${profilePreview(profile, state.run.values)}<div><span>Starting style</span><h2>${esc(profile.name)}</h2><p>${esc(profile.purpose)}</p></div></div></section>${pendingChanges()}<div class="session-scope"><strong>Current presentation</strong><span>These choices apply only here.</span></div><div class="design-settings">${styleCards(state.run, true)}</div>${assetsContent()}<div class="inline-actions"><button class="text-button" id="refresh-run-defaults">Update from profile</button><button class="text-button" id="reset-run-style">Clear presentation changes</button></div>`;
}

function renderPanel() {
  if (state.missingRun) {
    $("#session-content").innerHTML = '<div class="session-empty"><h1>Presentation unavailable</h1><p>Share its new folder location in the conversation.</p></div>';
    return;
  }
  if (!state.run) {
    $("#session-content").innerHTML = '<div class="session-empty"><h1>No presentation connected</h1><p>Open this panel from the presentation conversation.</p></div>';
    return;
  }
  $("#session-content").innerHTML = `<header class="stage-heading"><div><span>${esc(state.run.name)}</span><h1>Style and assets</h1><p>Inspect or adjust the visual settings used for this presentation.</p></div></header><div class="stage-content">${styleContent()}</div>`;
  applyPreviews();
}

async function refreshPanel(force = false) {
  if (!state.run) return renderPanel();
  if ($("dialog[open]") || document.activeElement?.matches("input,textarea,select")) return;
  const latest = await api(`/api/panel?run=${encodeURIComponent(state.run.path)}`);
  if (!force && latest.revision === state.panelRevision) return;
  state.run = await api(`/api/run?path=${encodeURIComponent(state.run.path)}`);
  sessionSnapshot = latest;
  state.panelRevision = latest.revision;
  renderPanel();
}

document.addEventListener("change", event => attempt(async () => {
  if (event.target.id !== "session-assets") return;
  for (const file of event.target.files) {
    await api("/api/upload", { run: state.run.path, filename: file.name, content_base64: await fileData(file) });
  }
  await refreshPanel(true);
  toast("Added");
}));

document.addEventListener("DOMContentLoaded", () => attempt(bootPanel));
