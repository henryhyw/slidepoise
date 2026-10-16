# Icon family and variant review

Use the enabled Remix Icon and Material Design Icons libraries for generic public icons. Fine is the default weight for generic line and outline icons. Compare candidates at the intended size. Use `resource-library.md` for retrieval. A generated generic icon can lead to a post-generation search across both libraries. Preserve a good composition while resolving its symbols to suitable assets.

## Remix Icon pairs

Read when generic public icons are useful. Remix Icon supplies most concepts as one 24 x 24 line/fill pair. When `remote_sources.remix_icon.enabled` is true, retrieve both official SVGs before generation with `scripts/fetch_remix_icon_pair.py NAME --config work/resolved-config.json --output-dir work/assets/remix`. Keep them in the run cache and retain the pair provenance.

The fetcher retains the untouched official files and derives `remix-NAME-line-fine.svg`. Its candidate ID is `remix-NAME-line-fine`. Use the returned manifest's candidate IDs and `canonical_file` paths throughout generation and reconstruction. The paired fill candidate keeps its original geometry. The Fine recipe moves filled boundaries inward by 0.35 source units, then uniformly restores the longest visible dimension and original bounds centre. Curves use a bounded 0.001-unit polyline approximation. This treatment reduces a representative 2-unit line to approximately 1.35 units after scaling. It does not author contour gaps or explanatory detail.

`remote_sources.remix_icon.line_weight` defaults to `fine`, including when older configuration files omit it. A session may set it to `original`. For a visually justified exception, pass `--line-weight original` to the fetcher and record the reason with the icon review. Preserve a coherent weight within each host-authored peer group. Do not silently use an old untreated cache entry as a Fine candidate. Re-fetch it through the packaged helper. Existing accepted presentations keep their bound artwork until explicitly revised.

The manifest records the recipe, source and derived hashes, engine versions, painted bounds, connected regions and holes. These are transformation facts. Inspect small details, joins, solid corners and any changed regions in the actual slide. Region or hole counts never decide visual acceptance. Unsupported SVG syntax or an empty result stops derivation with the original source retained. Inspect that source and explicitly choose Original or another suitable symbol. Do not silently fall back. The Logos category is preserved and reported as original artwork. Never apply Fine to exact brand marks or user-supplied canonical assets.

Both candidates belong on the generation context sheet. The context sheet does not select the winner. The image model may use either as visual vocabulary. After selecting the generated slide for reconstruction, inspect the actual icon slots and choose the canonical reconstruction variant.

## Material Design Icons through Iconify

When `remote_sources.mdi.enabled` is true, search the pinned collection with `scripts/fetch_mdi_icon.py --search "shield" --config work/resolved-config.json --output-dir work/assets/mdi`. Retrieve an exact name with `scripts/fetch_mdi_icon.py shield-check-outline --config work/resolved-config.json --output-dir work/assets/mdi`. The helper resolves name aliases and caches the versioned `@iconify-json/mdi` package inside the run. It checks the package against its pinned SHA-512 checksum before using cached or downloaded bytes. Retrieval then works offline from that verified cache. The browser catalogue and live API can help discovery, while the package provides repeatable artwork.

The default is `remote_sources.mdi.line_weight = fine`. The Fine recipe uses a 0.35-unit inset followed by extent restoration, producing approximately 1.35-unit outlines from a representative 2-unit source. MDI's `-outline` names receive Fine automatically. Solid icons keep their original geometry. For unsuffixed artwork such as a line drawing, visually inspect the source before explicitly declaring `--variant line`. Brand / Logo assets always retain their original geometry and identity. Use them through the exact image route when needed.

Fetch any useful solid or alternate outline candidate separately. MDI does not guarantee a line/fill pair for every concept. Keep the candidates in the generation context and record the chosen asset and visual observations after generation. Its manifest retains the source package, checksum, resolved name, author, Apache-2.0 license link, original SVG and source hash, derived hash, recipe and modification notice. `--line-weight original` preserves the heavier drawing when review calls for it. Never transform an already derived file again.

Prefer a coherent family within each peer group. When another library communicates a concept better, compare actual rendered shapes and use the same Fine weight, colour, slot size and alignment as its peers. Fine is a starting treatment. The host still judges small details, negative space and optical size in the slide.

## Custom line icons

Use the same Fine visual weight for custom-authored generic symbols. Identify the complete recurring family across the deck, including copies embedded inside larger illustrations. For SVGs with explicit strokes, adjust stroke widths in their own coordinate system while retaining paths, caps, joins, colour and placement. Compare their rendered weight and optical size with the other line icons at the intended slide scale. A source-unit width or fixed thinning percentage alone cannot establish consistency. Keep filled illustration regions and exact brand artwork intact, and retain the original asset beside each derived version.

When revising an existing deck's icon treatment, inspect every slide and trace each affected symbol through standalone and composite appearances. Update its current editing sources and preview assets together. Review the actual rendered pages after applying the shared treatment.

## Post-generation visual decision

Choose with the whole composition visible and inspect relevant close-ups. Consider these together.

- Apparent weight at the final slot size. Fine line details can collapse in a small slot. A filled mark can become visually blunt when enlarged.
- Foreground and background contrast after the profile treatment is applied.
- The surrounding visual grammar. Rules, outlined containers, sparse typography, and thin connectors often support line icons. Dense color fields, compact callouts, and strong focal emphasis may support fill icons.
- Local hierarchy. A fill icon may provide intentional emphasis. Do not use it merely because the icon is important semantically.
- Peer consistency. Icons in one `icon_treatment_group` use one variant and line weight. Create separate treatment groups when the composition calls for separate hierarchy levels.
- Silhouette fidelity. Select the variant whose mass, negative space, and optical footprint most closely match the approved target.

Do not reduce this choice to a score, background-color lookup, slot-size threshold, or automatic line-versus-fill rule. Code may verify that both candidates were considered and that peers agree. The Agent owns the choice.

For the chosen entity, record `icon_variant`, `upstream_asset_id`, and `icon_variant_review`. The review identifies the paired candidate asset IDs, states that it occurred after generation review, and gives concrete visual observations. The chosen `upstream_asset_id` must name the matching variant. Mechanical evidence establishes consistency and evidence presence only. It does not issue the visual verdict.

Remix icons may be recolored according to the active profile. Preserve aspect ratio and the selected candidate's geometry after the packaged Fine transformation or explicit Original choice. Do not thin an asset again during reconstruction or approximate it with an image-generation tool. Keep the official source unchanged beside the derived file. Do not use a generic Remix icon as a logo, trademark, or brand identity. Retain the Remix Icon License v1.0 notice and transformation provenance with fetched files.
