# Profile references, shared Library Sets, and current-chat resources

During a run, use `scripts/list_library.py --config work/resolved-config.json --query "keywords"`. This reads the captured profile, session-selected sets, provider switches and configured reference location used by generation. Resolve configuration again after settings change. Use `--profile <profile_id>` only to browse a shared profile outside a run. Filtering reduces recall only. The host Agent chooses by semantic and visual fit.

## Sources
- `<profiles-root>/<profile-id>/libraries/visual_references/catalog.json` contains style and communication precedents. Never copy their factual content by default.
- `<library-sets-root>/catalog.json` contains reusable icon and component set definitions.
- A profile's `library_sets.icons` and `library_sets.components` select complete sets. Different profiles may share the same set.
- Current-chat/user files: exact images, icons, logos, screenshots, and other assets supplied for the current slide.

## Profile-aware selection
Read `resolved_profile.visual_reference_priorities` after config resolution. Inspect relevant profile references first, then add slide-specific precedents when useful. A visual reference teaches visual language; semantic intent/user content still determines composition.

The host Agent selects resources by semantic role, visual fit, profile compatibility, identity requirements, and downstream reconstruction value. Do not turn selection into a numeric relevance winner. Respect configured budgets; user-required assets are exempt from the optional-asset cap.

Exact user-required assets override packaged alternatives. Brand identity requires an exact asset; never substitute a generic icon for a missing logo.

## Generation context sheet
After retrieval, the selected resource pool is consolidated into `work/generation-context-sheet.png` with `scripts/prepare_resource_context.py`.

Include:
- selected visual/style references;
- selected component previews;
- useful retrieved/packaged icon/image candidates;
- relevant user/current-chat uploads.

Show actual artwork. SVGs must be rendered to real previews; do not display an `SVG` placeholder.

The same sheet can be shown to the user when a style checkpoint would help and is passed to the image model. This keeps the visual direction and resource vocabulary consistent.

For each selected current-chat/exact identity asset:
1. inspect dimensions/aspect ratio when possible;
2. record exact canonical path and intrinsic ratio;
3. author a concise `generation_description`;
4. include it in the context sheet;
5. treat the generated depiction as composition guidance, not the canonical asset;
6. restore the exact file downstream using aspect-preserving contain-fit by default.

If a generated slot is materially incompatible with the canonical asset ratio, revise upstream composition rather than stretching the asset.

## Novel illustrations versus known assets
A profile may allow model-generated illustrations even when known reusable assets use a controlled vocabulary. This is not permission to invent substitute logos/icons/user images.

- Known and reusable visual identity comes from the selected resource pool.
- Novel illustrations are allowed only according to the active profile's `novel_illustrations` guidance and the slide's communication role.
- Novel illustrations must be semantically classified downstream and may enter the optional refinement branch.

## Icons
Use the existing `icon` / `icon_slot` path for icons and pictograms alike. Prefer profile-approved packaged icons when available. The logical icon slot is separate from any optional visible background surface. A generation-only localization boundary is scaffolding, not a reconstructable decorative box.

## Remote sets
Check `resolved_config.library_sets.selected` and `resolved_config.remote_sources` before any remote query. Remix Icon and Wikimedia identity assets are remote Library Sets. Selecting a set makes its provider available. A session may override its captured set selection without changing the profile. Profiles still govern visual treatment and appropriate use.

When the user requests a temporary source change, update that run's `library_sets` override and resolve the config again. Change the profile's selected sets only when the user wants the choice to recur. Trace which slides use the changed source and revise only those whose inputs changed.

- Remix Icon is the consistent generic-icon source. Fetch an official line/fill pair with `scripts/fetch_remix_icon_pair.py --config work/resolved-config.json`, keep both candidates in the run cache with provenance, and include both on the resource context sheet. Read `icon-variants.md` before choosing the post-generation reconstruction variant.
- Wikimedia Commons is the structured candidate source for exact logos and public media. Use `scripts/search_wikimedia_commons.py`, inspect the exact file page, then use `scripts/fetch_wikimedia_commons_asset.py` only after verifying identity, source, author, license, attribution, and trademark constraints. Commons availability does not itself grant trademark permission.

An official organization site or brand portal remains a valid exact-logo source when the active profile allows it. The Agent chooses an exact official HTTPS asset and records usage terms with `scripts/fetch_remote_asset.py`. If identity or permission cannot be verified, pause and ask the user. Persistent library updates require an explicit profile-maintenance request.

## Components
Components are design grammar, not fixed layouts. Select only when structurally useful, carry `component_id` + reason, pass the focused preview through the context sheet, and adapt sample content/counts/dimensions rather than copying them verbatim. Assign `component_id` downstream only when the accepted target actually uses that grammar.

Imported PPTX components retain their native source and selected page. Resource preparation renders a current preview of that page when needed. If the local renderer is unavailable, use the host's native renderer and supply the matching preview before generation. Image-only precedents remain image-only. Never describe them as editable PowerPoint components.
