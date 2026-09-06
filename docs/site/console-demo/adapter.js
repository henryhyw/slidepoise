/* Demo-only transport. The production Console is copied unchanged apart from its API function. */
(() => {
  const data = structuredClone(window.consoleFixtures);
  delete window.consoleFixtures;
  let revision = 1;
  const originals = structuredClone(data.designs);
  const clone = value => structuredClone(value);
  function design(id) {
    const result = data.designs[id];
    if (!result) throw new Error('Choose a sample profile.');
    return { ...clone(result), active_profile: data.overview.active_profile, profiles: clone(data.overview.profiles),
      revision: String(revision), profile_revision: String(revision), style_agency: clone(data.profiles[id].profile.style_agency), library_sets: clone(data.libraries.sets) };
  }
  window.consoleDemoAPI = async (path, body) => {
    const url = new URL(path, 'https://demo.invalid');
    const id = body?.profile || body?.profile_id || url.searchParams.get('profile') || data.overview.active_profile;
    if (body !== undefined) {
      if (url.pathname === '/api/profile') data.overview.active_profile = body.profile_id;
      else if (url.pathname === '/api/profile/style') {
        if (body.revision !== String(revision)) throw new Error('This demo changed. Reopen the setting and try again.');
        Object.assign(data.designs[id].values, body.values);
        const fields = body.profile_values || {};
        if (fields.style_agency) Object.assign(data.profiles[id].profile.style_agency, fields.style_agency);
        if (fields.library_sets) { data.profiles[id].profile.library_sets = clone(fields.library_sets); data.designs[id].selected_sets = clone(fields.library_sets); }
      } else if (url.pathname === '/api/design' && body.reset) data.designs[id] = clone(originals[id]);
      else if (url.pathname === '/api/profile/update') Object.assign(data.profiles[id].profile, body.values);
      else if (url.pathname === '/api/profile/create') {
        const key = 'demo-' + revision;
        const source = body.based_on || data.overview.active_profile;
        data.profiles[key] = clone(data.profiles[source]);
        data.profiles[key].id = key;
        Object.assign(data.profiles[key].profile, {profile_id: key, name: body.name, purpose: body.purpose});
        data.designs[key] = clone(data.designs[source]);
        data.designs[key].values.profile = key;
        originals[key] = clone(data.designs[key]);
        data.references[key] = clone(data.references[source]);
        data.overview.profiles.push({...clone(data.overview.profiles.find(item => item.id === source)), id: key, name: body.name, purpose: body.purpose});
        data.overview.active_profile = key;
        revision++;
        return {profile: {...clone(data.profiles[key]), name: body.name}};
      } else if (url.pathname === '/api/profile/reference/update') {
        const item = data.references[id].items.find(item => item.id === body.id);
        Object.assign(item, body.values);
      } else if (url.pathname === '/api/library-set/update') {
        Object.assign(data.sets[body.set_id], body.values);
        Object.assign(data.libraries.sets.find(item => item.id === body.set_id), body.values);
      } else if (url.pathname === '/api/profile/reference/add' || url.pathname === '/api/library-set/add') {
        if (!/\.(png|jpe?g|webp)$/i.test(body.filename)) throw new Error('This demo accepts PNG, JPEG and WebP images.');
        const mime = /\.png$/i.test(body.filename) ? 'image/png' : /\.webp$/i.test(body.filename) ? 'image/webp' : 'image/jpeg';
        const item = {id: 'upload-' + revision, name: body.name || body.filename, description: body.description || '', asset_url: `data:${mime};base64,${body.content_base64}`};
        const library = body.set_id ? data.sets[body.set_id] : data.references[id];
        library.items.push(item); library.count = library.items.length;
      } else if (url.pathname === '/api/library-set/create') {
        const item = {id: 'demo-set-' + revision, name: body.name, kind: body.kind || 'icons', description: body.description || '', source: 'local', items: [], count: 0};
        data.libraries.sets.push(item);data.sets[item.id] = item;
      } else throw new Error('This action is available in the installed Console.');
      revision++;
      return url.pathname === '/api/profile/style' ? design(id) : {profile: clone(data.profiles[id]), overview: clone(data.overview)};
    }
    if (url.pathname === '/api/overview') return clone(data.overview);
    if (url.pathname === '/api/console/revision') return {revision: String(revision)};
    if (url.pathname === '/api/design') return design(id);
    if (url.pathname === '/api/profile') return {...clone(data.profiles[id]), revision: String(revision)};
    if (url.pathname === '/api/library') return {...clone(data.references[id]), revision: String(revision)};
    if (url.pathname === '/api/library-sets') return clone(data.libraries);
    if (url.pathname === '/api/library-set') return {...clone(data.sets[url.searchParams.get('set_id')]), revision: String(revision)};
    if (url.pathname === '/api/health') return clone(data.health);
    if (url.pathname === '/api/settings') return clone(data.settings);
    if (url.pathname === '/api/component') {
      const set = data.sets[url.searchParams.get('set_id')];
      const component = set.items.find(item => item.id === url.searchParams.get('id'));
      return {component, set_id: set.id, native: false, note: 'This sample component describes a reusable slide structure.', catalog_revision: String(revision)};
    }
    throw new Error('This view is available in the installed Console.');
  };
})();
