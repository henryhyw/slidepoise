# Multi-Agent Review

Use this review layer when the host exposes subagents and an independent reading would materially help. It supports deck planning, selected page reviews, and final consistency review without imposing a fixed checkpoint sequence.

## Operating model

The root Agent remains the SlidePoise host Agent and owns the final decision. A reviewer is a bounded, read-only critic. It inspects named artifacts and returns findings. It never edits the run, selects resources, generates an image, or accepts visual quality.

For deck production, a worker may own one isolated slide directory while the parent retains the outline and shared presentation state. Within one slide, keep dependent stages together. Use separate read-only reviewers where an independent reading can expose an omission or mistaken assumption.

## Parallel specialist work

Delegate independent work when useful, including candidate asset retrieval, evidence verification, bounded copy review, SVG illustration construction and page-local reconstruction. Keep dependent decisions sequential. The host owns the communication intent, selected content, shared style, object placement and final acceptance. A specialist may propose a better treatment without silently changing those decisions. Give each writing worker an isolated asset directory or page directory so parallel work cannot overwrite another worker's scene or shared configuration.

An SVG specialist needs the communication context, not just a crop. Supply the slide's claim, the visual's explanatory job, the surrounding page, the target slot and style, plus the details that carry meaning. Distinguish exact identity and factual constraints from incidental texture or decorative details that may be simplified. Name visible source defects separately in the handoff, including any white pinholes, speckles or malformed details that must be repaired. Do not send an unqualified instruction to copy the source faithfully when it contains defects. The specialist may reinterpret a difficult illustration when the new geometry preserves its purpose. It must report any omitted detail and why that omission is harmless, and flag any simplification that changes the meaning. Exact logos remain sourced assets.

Ask the specialist for the SVG, a rendered preview at intended size and an enlarged detail, its provenance and a brief account of preserved and simplified features. The host inspects those outputs in the actual slide, then selects the asset and binds it through the normal semantic-map and reconstruction path. Do not accept a vector merely because it is syntactically valid or resembles the crop in isolation. A specialist that finds the current asset already suitable can return that judgement without manufacturing another version.

## Review checkpoints

### Plan review

For a content-first pitch review, first give the reviewer only the audience and proposed reader-facing copy. Ask what business opportunity, action and value the text itself establishes. The reviewer must flag any relationship it had to infer from unstated project knowledge. Do not supply the author's intended interpretation until after that reading. Then compare the observed understanding with the brief. This review cannot substitute for a user-requested content approval.

Give the reviewer the user request, resolved profile, relevant profile guidance, and draft slide intent. Ask it to find:

- missed or contradicted user instructions
- missing front-half workflow stages such as communication planning, profile resolution, or retrieval
- claims unsupported by the current project
- premature layout restrictions unsupported by the user's requirements or inspected design evidence
- wording that would fail in the intended publication context

The reviewer must distinguish communication structure from visual layout. The initial intent defines hierarchy, relationships, evidence and obligations. A user-specified layout is a requirement. An Agent may develop a composition within the authorised brief after inspecting resources and exploring the visual argument. Check its reasoning and remaining freedom, and keep the selected direction in `style_direction`. Challenge unsupported restrictions without requiring the user to approve routine design choices.

### Evidence and inference review

When a central pitch claim depends on research, give an independent reviewer the claim, displayed evidence and primary source passages. Ask whether the evidence establishes the premise, the proposed mechanism or an actual outcome, and which link remains an inference. Test a plausible counterexample in which the statistic remains true while the proposed benefit does not follow. An aggregate average may conceal the variation a proposed intervention needs. Accurate numbers and clear labels do not repair that logical gap.

Require a finding to name the unsupported link and its consequence for the reader. Distinguish a real inferential error from an omitted detail that the pitch does not need. The host evaluates each challenge against the source and communication purpose, corrects valid gaps, and retains sound content when the critique is overly broad or immaterial. Record a concise evidence-based disposition. Do not turn every possible qualification into visible defensive copy. A relevant qualitative precedent can be stronger than an impressive but irrelevant statistic.

### Style and asset review

Give the reviewer the original request, relevant source materials or project paths, enabled libraries and profile, plus actual page images when available. First ask what identity, evidence or explanatory resources the content warrants. The reviewer should inspect concrete candidates where an omission is plausible and identify pages that benefit from typography or native geometry alone. Then provide the current plan, resource selection and context sheet for comparison. Keep the author's selection reasons and acceptance statements out of the first reading so they cannot define the reviewer's entire scope.

Check both unnecessary assets and missed opportunities supported by the source. Distinguish a user obligation from an Agent proposal. Challenge proposals that prematurely narrow the visual design, including unsupported rejection of an entire resource class. Cite the source asset and the communication role it could serve. Do not recommend icons merely to increase their count. Reuse the existing finding format and revise the existing plan or selection when warranted.

For central named firms or products, check whether the author inspected relevant identity candidates before omitting them. For the composition, ask what the visual helps a cold reader infer beyond the prose. Challenge a familiar table or panel structure when it only mirrors the outline, and retain it when aligned comparison is the explanatory job. Look for meaningful exploration in the actual references, candidate assets and visual alternatives. A populated selection field or attractive typography alone does not establish that work.

### Semantic-map review

Give the reviewer the accepted slide, semantic map, reconstruction handoff, and profile. Ask it to inspect meaningful object coverage, render ownership, intrinsic raster lettering, connector semantics, typography and icon peer groups, canonical asset mappings, and likely reconstruction failure modes.

### Reconstruction review

First give the reviewer the intended audience and actual page image, without the author's intent or explanation. Ask for the meaning they can establish from that page and any context they had to assume. For an unfamiliar journey, this includes the initial need, actor-owned actions and resulting change. Use this first reading to expose missing context before the brief supplies it.

Then give the reviewer the original intent, accepted slide, visual comparison, constructor scene, reconstruction contract and rendered-text evidence. Ask it to identify missing meaning, defects already in the generated design, material visual differences, editability losses, unexplained rasterization, connector defects, text fitting problems, and unsupported patch coordinates. Keep the author's acceptance statements and proposed fixes out of the first reading. The reviewer must open the images and cite visible evidence. Reading the review JSON is insufficient.

Do not stop after confirming that all required content is present and nothing overlaps. Ask the reviewer to state the fact conveyed by each prominent metric without supplying a definition, trace shared connectors from their source through the junction, compare the local spacing of adjacent content regions and inspect retained small artwork in detail. Report useful minor polish findings separately from material defects. A broad acceptance sentence must not erase a concrete readability or finish issue.

Judge the source composition on its own before using it as a reconstruction benchmark. Identify crowded labels, empty nominal stages, weak balance or an unclear visual argument even when both images share the same defect. A favourable fidelity comparison does not accept a weak design. If the source is rejected, report a design revision and stop treating it as the quality target.

A reconstruction reviewer needs both the accepted target and the current native content crop at equal scale. Supply them directly, not only as optional files to open if something looks wrong. Ask for observed differences in type scale and weight, line wrapping, colour, background-field geometry and alignment before any acceptance statement. Classify authorised copy changes separately from visual drift. The host also checks the comparison and owns the result. Do not convert a native-only readability check into a fidelity approval.

Calibrate proposed improvements to the page’s communication job. A conceptual illustration may support prose without functioning as a fully specified data diagram. Add a legend when a reader needs it to understand the claim or the relationship. Do not replace an accepted explanatory visual with generic labelled boxes merely to make every mark literal. Judge the proposed replacement in context and retain the baseline when the intervention creates greater abstraction or reading burden.

### Cross-page visual calibration

Give the reviewer the user requirements, shared deck design, resolved frame and the actual page images together. Generated candidates reveal design drift before reconstruction. Final rendered pages reveal typography and frame drift introduced during construction.

Ask for direct peer comparisons across claim titles, subtitles, supporting text, table headings, data labels and recurring decision treatments. Check font family, apparent size and weight, alignment rhythm, accent meaning, fills and rules. Confirm that generated images exclude the inherited frame and that rendered pages share it. A visually intentional exception needs a communication reason.

For peer titles, compare actual emitted point sizes as well as the rendered pages. A differing generated title size is not an intentional exception by itself. After a correction, inspect whether the reclaimed space was rebalanced or left as an unexplained hole.

The reviewer must identify the specific pages and roles that differ. It must not infer consistency from separate page approvals, a shared Profile name, identical config hashes or aggregate object counts. Mechanical style facts may assist the comparison. The visual judgement remains with the Agent.

## Choose reviewers for the uncertainty

A fresh reviewer is useful when reconstruction, dense relationships, a substantial local edit or repeated user feedback creates a specific risk that the author has missed. Assign a narrow question and the actual visual evidence. Routine changes with a clear inspected result do not need another worker. More agents repeating the same general review can add cost without improving coverage.

For layout uncertainty, separate two readings. A cold reader opens the native slide alone and identifies unclear meaning, competing emphasis and local crowding or empty space. A reconstruction reviewer then compares the accepted substantive region with the native content crop at the same scale, region by region. Ask what changed in line breaks, optical footprint, gaps, visual weight, asset quality and connector attachment. A difference is evidence to inspect, not automatically a defect. The host distinguishes authorised revisions and useful corrections from accidental drift.

These readings can be performed sequentially by one independent reviewer. When the deck warrants parallel review, divide the work by distinct uncertainties or isolated page ranges and keep shared-scene edits with one owner. Give reviewers current images and source inputs, not another agent's favourable verdict. Use enlarged details only where presentation-scale review leaves a question unresolved.

Return a bounded set of specific findings with page or region, visible evidence, the reader consequence and a targeted remedy. Record which regions were actually inspected and any limitation. The host resolves the findings, rerenders the changed slide, then checks that region and its neighbours for secondary effects. Broaden the review only when the correction changes a shared role, the narrative, or dependent relationships. Stop when the identified defects are resolved and the current artifact has been inspected. Review coverage improves with complementary readings, but no agent arrangement guarantees discovery of every visual defect.

## Finding contract

Each finding contains:

- `id`
- `severity` as `material`, `important`, or `minor`
- `criterion`
- `evidence`
- `recommended_action`

The root Agent records one disposition for every material or important finding:

- `accepted` with the resulting revision
- `rejected` with concrete evidence
- `deferred` only when user input or an unavailable dependency is genuinely required

For plan, resources, and semantic mapping, use one independent review followed by one root-Agent correction pass. Do not create an open-ended critic loop. After the correction, the root Agent checks that the cited issues were addressed and continues. If a material disagreement requires a new user decision, stop and ask the user.

Reconstruction is stricter because the released PowerPoint must have no unresolved material visual issue. A reviewer may inspect visual fidelity while another inspects editability, text, connectors, and raster boundaries. Corrections remain focused on concrete findings. After two unsuccessful correction rounds, revisit the relevant upstream artifact. Ask the user only if the remedy changes an agreed requirement or needs an unavailable capability. Repeated failure is a reason to reconsider the approach, not to keep making local adjustments or hand routine debugging to the user.

## Availability fallback

If subagents are unavailable, the root Agent may perform the same checklist in a separate review pass. Lack of subagents never blocks sequential page work or delivery.

## Limits

Multi-Agent review improves coverage. It does not guarantee correctness. Evaluate it against real SlidePoise cases and track whether it catches known failures without producing excessive false alarms.
