---
name: slidepoise
description: "Create one slide or a complete polished presentation as editable PowerPoint. Use when the host Agent must plan a flexible deck, generate or edit slide designs, reconstruct native PowerPoint objects, revise individual slides, reorder or remove slides, and visually verify the result."
---

# SlidePoise

Act as the host Agent for presentation creation. Infer whether the user wants one slide, several slides, or a complete deck. Use one adaptable workflow for every scope. Do not ask the user to choose a product mode.

Own interpretation, communication design, deck structure, resource choice, image-generation orchestration, every visual judgement, semantic mapping, reconstruction intent, review, revision, and delivery. Use deterministic code for measurement, transformation, fitting, construction, packaging, and objective file facts. A script never decides whether a slide is beautiful, readable enough, faithful enough, or ready to release.

## Absolute authority rule

If answering a question requires looking at a slide, look at the slide and reason visually. Never replace that judgement with a score, confidence threshold, object count, whitespace metric, minimum font size, file-presence rule, or heuristic pass/fail.

OpenCV is mandatory pixel evidence during editable reconstruction. The Agent says what an object is, which region it owns, and which measured geometry needs correction. OpenCV does not choose semantic ownership, alignment, or visual acceptance.

## Reconstruction path invariant

After selecting `accepted-slide.png`, every delivered editable slide must pass through the packaged reconstruction path. Author the semantic map and reconstruction handoff, run packaged OpenCV measurement, inspect the overlay, build the reconstruction contract, compile the constructor scene, and render through `scripts/slidepoise_runtime.py`.

The generated image contains the substantive content region only. Header, footer, page numbers and shared frame rules belong to the inherited PowerPoint frame. Resolve that frame before generation and derive the content aspect ratio from the full slide minus the enabled frame heights. A 16:9 PowerPoint does not imply a 16:9 generation canvas. Disabling a frame removes it from the presentation and never transfers its content into image generation.

Submit the compiled generation request through the host image tool. Do not prepare an authoritative brief and then replace it with a separately written prompt. Change intent, resources or shared design decisions upstream and compile again when the prompt needs revision. Visually check the returned canvas and excluded frame content before semantic mapping.

Do not write a custom PptxGenJS, python-pptx, HTML, SVG, or other direct deck builder as a substitute. Do not redraw the generated target from memory or guessed coordinates. PptxGenJS is an implementation detail behind the packaged scene renderer. If a required reconstruction artifact or command is unclear or fails, inspect the packaged schema and command help, then repair the input or report the exact blocker. Never silently switch reconstruction methods.

## Read before working

At the start of every run

1. Resolve the SlidePoise CLI once. Use `slidepoise` when it is on `PATH`. Respect `SLIDEPOISE_HOME` when it is set. Run `doctor` and `profile show` to locate the framework home and active external profile.
2. Read the external framework config, selected profile, and its selected Library Sets. Profiles, visual references, icons, and components never live inside this skill.
3. Resolve current-presentation overrides with `scripts/resolve_config.py`.
4. Read `references/deck-orchestration.md`, `references/workflow.md`, and `references/runtime-host.md`.
5. Read `references/human-approval.md` for adaptive user checkpoints. It does not define mandatory gates.
6. Read `references/resource-library.md` before resource selection.
7. Before semantic mapping or reconstruction, read `references/visual-reasoning.md`, `references/connectors.md`, and `references/reconstruction.md`.
8. Read `references/raster-composition.md` for raster artwork, intrinsic lettering, texture, or overlapping text. Read `references/illustration-refinement.md` before an optional raster edit.
9. Read `references/multi-agent-review.md` only when parallel page work or independent review would materially help and the host exposes subagents.
10. Read `references/user-language.md` before authoring user-facing prose.

## Product shape

- Conversation is the primary control surface. Present outlines, context sheets, generated slides, comparisons, and final files directly in the conversation.
- The optional session panel is a lightweight editor for current-presentation style and asset overrides. Open it only when the user asks to inspect or adjust those settings, or when a visual control would clearly help.
- The optional Console manages reusable Profiles, Library Sets, and local capabilities. It does not manage presentation projects or run history.
- A run directory is an implementation workspace. Do not make the user manage it.
- One slide is a deck with one ordered slide entry. Multi-slide work uses the same contracts and the same reconstruction pipeline per slide.

## Adaptive collaboration

Infer the amount of interaction from the user's request.

- If the user asks for a fully automatic deck, clarify only material ambiguity, agree on the brief when needed, then continue through the deck without per-slide approval.
- If the user wants close direction, show the outline, style direction, sample, or selected slide candidates at useful moments.
- If the user requests one slide, avoid deck-management ceremony.
- If a decision would materially change the message, audience, required evidence, brand identity, cost, or number of creative calls, ask before making that decision.
- User feedback can add, remove, reorder, merge, split, or revise slides at any time. Update the deck outline and only invalidate affected downstream artifacts.
- Never require a plan, resource, image, or illustration approval record as a condition for continuing. Record important user decisions when they exist so later work can respect them.

## Deck model

Author `work/deck-outline.json` for any presentation, including a one-slide presentation. Use stable slide IDs and an explicit ordered list. Each entry records the slide role, communication job, dominant message, content obligations, evidence and asset obligations, dependencies, and current disposition.

Store page-local artifacts under `slides/<slide-id>/work/` and deliverables under `slides/<slide-id>/deliverables/`. Shared configuration, deck-wide resources, the outline, and deck-level review artifacts remain at the run root.

The outline is live. When the user or Agent revises the deck

- preserve IDs for unchanged slides
- create new IDs for genuinely new slides
- mark removed slides as omitted or move their folders to an archive without deleting evidence
- reorder through the deck outline instead of renaming slide folders
- invalidate only artifacts whose inputs changed
- re-evaluate transitions and deck-level consistency after structural changes

Read `references/deck-orchestration.md` for the complete contract.

## Core workflow

1. Understand the source, audience, purpose, desired scope, evidence, constraints, and user assets.
2. Create or revise the deck outline. For a single slide, keep this compact. For a deck, plan the narrative arc and each slide's communication job before detailed slide composition.
3. Resolve the Profile and current-presentation overrides once. Inspect the enabled visual libraries against the deck's communication jobs before accepting an empty resource selection. Select shared references and reusable resources at deck level, then add page-specific resources where they clarify meaning or preserve identity. Record why each resource class was used or left unused.
4. Decide the useful collaboration checkpoints. A sample slide is often helpful for a large or visually uncertain deck. It is optional.
5. Establish the deck's shared visual decisions using `references/deck-orchestration.md`. Discover recurring visual functions from the actual pages and references, including small recurring marks. The role inventory stays open as generated candidates and native renders reveal new peers. Map each role to page-local entity aliases and materialize its chosen treatment in those entities. For each active slide, author its intent and generation context, generate or edit one substantive-region design, inspect it against the shared direction, then reconstruct it with the page-local pipeline in `references/workflow.md`.
6. Process independent slides concurrently when the host supports it. The parent Agent owns the outline, shared style, cross-slide consistency, ordering, and final assembly. A page worker owns only its slide directory.
7. Compile one constructor scene per active slide through the packaged reconstruction path. Assemble only those compiled scenes in the current outline order with `slidepoise_runtime.py render-deck`.
8. Render and inspect every slide, using the contact sheet to find recurring elements and full-resolution pages plus native style facts to compare them. Look for undeclared peers as well as already named roles. Series labels, captions, source lines, section markers, folios and other minor recurring elements need the same attention as dominant text. These examples are not a whitelist. The Agent decides peerhood, applies shared treatments or explicit exceptions, and reviews the result. A successful page-local fit or review does not establish cross-page consistency. Review narrative continuity, pacing and transitions as well, and repair affected slides before accepting the assembled deck.
9. Deliver the final editable `.pptx`, useful preview artifacts, and a concise note about any meaningful raster regions or limitations.

## Per-slide reconstruction

The generated or user-approved slide image is the visual target for reconstruction. Inspect it and author meaningful PowerPoint-level entities, logical text regions, canonical asset mappings, connector semantics, and raster-source classes.

For a generated target, those coordinates belong to the substantive region. The compiler maps that region into the full slide using the resolved frame offset. Add shared header and footer content through the inherited frame after construction. Compare the generated target with the corresponding content crop of the actual render, then inspect the whole assembled slide for frame placement and cross-page consistency.

Use OpenCV to collect geometry, color, contour, text-ink, and crop evidence. Apply geometry corrections only after visual inspection. Build the reconstruction contract, compile the constructor scene, render the PowerPoint, and compare the render with the target. Reconstruction translates the target into editable objects. It does not redesign the slide.

Use native PowerPoint text, shapes, tables, charts, connectors, and editable freeforms when faithful. Use raster images for genuine photos, textured regions, and illustrations whose decomposition would invent unsupported structure. Preserve exact user assets and canonical logos.

## Objective blockers

Deterministic tools may stop execution for objective failures such as malformed contracts, missing referenced files, invalid coordinates, stale input bindings, corrupt PowerPoint packages, broken media relationships, or an output that cannot be opened.

Deterministic tools must report evidence without blocking on aesthetic preferences such as font size, density, whitespace, balance, alignment taste, illustration quality, or visual similarity. The host Agent inspects those facts and decides what to do.

## Visual reviews

Create host-Agent review records for generated designs, measurement overlays, reconstructed slides, and the assembled deck when those artifacts exist. Bind the exact files that were inspected. Records capture observations and decisions. They are not script-issued scores.

For a multi-slide deck, use contact sheets or grouped comparisons when they make consistency easier to judge. Inspect full-resolution pages whenever a contact sheet hides a material detail.

## Runtime

- ChatGPT uses the native image-generation or editing capability.
- Codex uses the available image-generation skill or tool.
- Use the framework's Python and OpenCV scripts for measurement and raster operations.
- Use the packaged scene renderer, which uses Node and PptxGenJS internally, for editable PowerPoint construction. Do not invoke PptxGenJS directly for a presentation run.
- Prefer `scripts/slidepoise_runtime.py render-preview` when LibreOffice is available.
- Use `scripts/slidepoise_runtime.py render-deck --manifest work/deck-scenes.json` to assemble ordered slide scenes.

## Flexible design rules

- Explicit user requirements take precedence over packaged defaults when feasible.
- Density is qualitative guidance. It is never an occupancy score or a font-size gate.
- Preserve compositional freedom. Do not force grids, cards, chart types, connector families, or rounded corners unless the content, profile, or user calls for them.
- Keep a coherent deck-wide visual identity while allowing layouts to vary with slide role.
- Never synthesize or approximate an exact logo or required user asset.

## Maintenance

When changing this skill or framework, read `references/maintenance.md`, keep runtime mechanics separate from Agent judgement, and run the packaged validators.
