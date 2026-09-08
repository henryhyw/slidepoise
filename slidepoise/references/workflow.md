# SlidePoise page workflow

This page-local workflow is reusable inside a one-slide request or a larger deck. Paths below are relative to `slides/<slide-id>/` for a deck and relative to the run root for legacy one-slide runs.

## 1. Resolve intent

Author `work/slide-intent.json` from the corresponding entry in `work/deck-outline.json`. Capture the audience question, dominant message, exact content, semantic relationships, hierarchy, evidence and source obligations, required assets, exclusions, assumptions, and unresolved questions that affect this page.

Do not force a numbered process unless the information is sequential. Do not prescribe a detailed layout before resources and visual reasoning unless the user already did.

## 2. Resolve configuration and resources

Use the deck's resolved configuration and shared resource selection. Add page-specific visual references, icons, components, images, or user assets only where they help this slide.

Before writing the resource selection, make a visual-role pass over the slide intent. Look for concepts that would be read faster or remembered more clearly with a known icon, exact identity asset, reusable component, photograph, or other visual resource. Inspect the libraries that are actually enabled. Do not infer that an empty `asset_obligations` array means no assets can help. Record the decision for each relevant resource class in `selection_reasoning`, including a concrete reason when the selection remains empty. A multi-slide run with an enabled icon library and no selected icons on any page deserves a second deck-level review before generation. Icons remain optional. The Agent decides whether they improve the communication.

For a deck, read the same `work/deck-design.json` used by the other pages. Its recurring visual roles are host-authored decisions. Preserve them during page work and return a proposed change to the deck owner when an exception is needed.

Resolve header and footer settings before preparing the generation context. The substantive canvas has the full slide width and the full height minus enabled header and footer heights. The header and footer are constructed later as inherited frame content. Do not put their wording, page numbers or rules in the page's visual obligations. A footer-like qualification that is essential to this page's argument remains substantive content and must have an explicit content role distinct from the shared frame.

Author `work/resource-selection.draft.json`, then run `scripts/prepare_resource_context.py`. The generated context sheet is an input to image generation and an optional review artifact for the user. It is not an approval token.

When a selected visual reference needs readable typography or fine detail, set its `full_resolution_attachment` to `true` to attach its canonical image with a verified hash after the context sheet, in selection order, even under `full_context_sheet`. The default is `false`, and this reference choice is independent of canonical asset attachment policy.

## 3. Prepare and generate the visual target

Run `scripts/prepare_generation.py` to compile the resolved canvas, profile guidance, intent, resources, shared deck design and generation budget into the contract, brief and `work/generation-request.json`.

Pass the request's prompt to the host image capability without rewriting it. Attach the recorded reference images using the host's supported mechanism. Save the actual call and returned image reference when the host exposes them. A missing tool capability is a host integration issue, not permission to use a separate construction path.

Generate one purposeful substantive-region candidate. Visually inspect its content, frame exclusion and aspect ratio. Compare repeated title and body styles, accent meanings and recurring treatments with the shared deck direction and earlier accepted candidates. If it misses the communication job or has a material visual defect, make a focused edit or regenerate. Update the upstream inputs and recompile when changing generation instructions.

For a focused candidate edit, record the corrections from Agent review or user feedback in `work/image-edit-changes.txt`. Run `python scripts/prepare_image_edit.py --generation-request work/generation-request.json --candidate work/candidate.png --changes work/image-edit-changes.txt --output work/image-edit-request.json`. The request retains the verified substantive canvas, shared design and reference images, binds the candidate pixels and corrections, and applies the generation host's prompt capacity without truncation. Immediately before calling the image capability, run `python scripts/prepare_image_edit.py --verify-request work/image-edit-request.json`, then pass its prompt unchanged with its ordered reference images. The first image is the candidate to edit. Agent review can initiate this correction without a separate user request. A change to source intent or shared design requires recompiling the generation request first. Inspect the returned image before accepting it.

Never repair a wrong aspect ratio by stretching the target. If a model adds removable frame content or returns a different canvas, the Agent may define a crop after inspecting it and use `scripts/normalize_generation_canvas.py` to fit that crop without distortion. Otherwise regenerate. Review the resulting image again before mapping semantics.

Show the image when the user asked to review slides, when their feedback would prevent material rework, or when the result is useful progress to share. A fully automatic request authorizes the Agent to continue after its own review.

Freeze the selected target as `accepted-slide.png`. Here, accepted means selected by the Agent or user for reconstruction. It does not imply a mandatory user gate.

Compare available candidates together and revisit the deck's role inventory. Identify repeated visual functions that emerged in generation, including peripheral labels, captions and series markers that were absent from the initial brief. Give their page-local aliases and chosen treatment to the deck owner before independent reconstruction carries the drift forward.

## 4. Map semantics

Inspect the selected target and author `work/semantic-map.json` plus `work/reconstruction-handoff.json`.

Map meaningful PowerPoint-level entities, logical text regions, text hierarchy, icon slots, canonical assets, connector semantics, and raster-source classes. Every emitting entity has an explicit geometry policy and z layer. Keep semantic role separate from visual style role.

Read the current `deck-design.json` and resolve its recurring roles to the page's actual entities. Apply the chosen styles to `style_hint` or explicit compatible config tokens, and retain `recurring_role_bindings` with the source design in the handoff. Role bindings describe the decision and its recipients. They do not apply styles automatically. A local fitting group describes that page's fitting scope and cannot establish consistency with another page. Report newly discovered peers and any proposed exception to the deck owner.

Run `scripts/collect_semantic_evidence.py` to collect objective structural facts. The Agent consumes the evidence and owns the semantic decision.

## 5. Resolve raster sources

Inspect novel illustrations and textured regions at intended output size. Reuse adequate crops. Use a focused image edit when it materially improves a selected raster source. Ask the user only when the extra call, identity change, or visual tradeoff needs their decision.

A refined raster changes its pixel source only. The target bbox remains tied to the selected substantive-region composition.

## 6. Measure

Run OpenCV measurement with the active semantic map. The Agent inspects the target and overlay, chooses ownership, and authors any geometry corrections. No script discovers visual peers or chooses an aesthetic alignment.

Use the packaged command below for the deterministic reconstruction stages. It always runs OpenCV measurement before it builds the reconstruction contract and constructor scene.

```bash
python scripts/slidepoise_runtime.py reconstruct-slide \
  --image work/accepted-slide.png \
  --semantic-map work/semantic-map.json \
  --upstream-handoff work/reconstruction-handoff.json \
  --config ../../work/resolved-config.json \
  --slide-id <stable-slide-id> \
  --output-dir work/reconstruction
```

Inspect `work/reconstruction/measurement/debug_overlay.png` against the accepted target. If semantic ownership or geometry needs correction, update the semantic map and run the same command again. The authoritative outputs are `measurement/slide_entities.json`, `reconstruction-contract.json`, and `constructor-scene.json`.

## 7. Reconstruct

Build the reconstruction contract from the measured scene and resolved config. Compile one constructor scene for the slide. Restore exact assets, fit declared typography groups, reconstruct native objects, preserve meaningful raster regions, and bind connectors to their semantic owners.

The packaged command above performs these deterministic build steps. Do not replace them with a custom direct PowerPoint construction script.

## 8. Render and review

Render the page or assembled deck and compare the reconstructed slide with its selected target. Inspect fidelity, hierarchy, asset treatment, text fitting, connector routing, collisions, density, whitespace, and editability.

Use the configured content crop for target comparison and the whole slide for frame review. Header and footer text, rules and page-number fields must come from the shared inherited frame. They must not be duplicated as image content or page-local substitutes.

Keep cross-page typographic peers at the deck's chosen size and treatment. Inspect native style facts and the actual images for every discovered role, including small recurring labels or marks. Revisit the inventory for undeclared peers after rendering. If a member no longer fits, the Agent should reconsider its allocation, wording, line breaks or shared role scale while preserving the message. Do not silently shrink that member and call the role consistent. An exception is possible when the Agent records its actual members, chosen treatment and purpose, then visually reviews it across the deck.

Fix objective runtime defects directly. For a visual issue, decide whether the correction belongs in the semantic map, measurement interpretation, generated target, or deck outline. Do not add arbitrary final coordinates to generic runtime code.

## 9. Return to deck orchestration

Return the page scene path and current artifact bindings to the deck owner. A page worker writes only its assigned page directory. The parent Agent updates the shared `work/deck-scenes.json`, assembles active slides in outline order and performs the deck-level sequence review described in `deck-orchestration.md`. A sequential host performs both responsibilities itself.
