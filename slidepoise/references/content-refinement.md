# Optional content refinement

Use this workflow when the user asks for better client-facing content, when a consulting deliverable needs a content review, or when authorised wording must be improved without changing the design. Use the available `consulting-content` skill for its reader and meaning judgement. If unavailable, apply the existing user-language contract and task context. Its absence does not block ordinary slide work.

## Ownership

The companion skill proposes copy and identifies ambiguities. SlidePoise owns the slide composition, resource selection, geometry, text fitting, reconstruction and final render review. Preserve the user's latest designated deck and firm template. Do not restore old generated headers or footers over user-supplied frame elements.

Keep this optional. Exact-copy reproduction and already approved copy do not need compulsory rewriting. Source research remains a separate task when the user has deferred it.

## Before image generation

Establish the message through actual draft copy before requesting a composition. For a new pitch or a full restart, explain the opportunity, the product's action and the value in language an unfamiliar reader can follow. A populated intent schema or a set of section headings does not establish that understanding. Reject copy that works only when the author adds an oral interpretation. Keep internal research and evaluation commentary separate from audience-facing prose unless it changes a decision the audience needs to make.

Check the dominant message separately from topic coverage on every page. Read only the proposed audience-facing copy, state the conclusion it actually supports, then compare that reading with the intended conclusion. Supporting classifications, examples or technical detail must not displace the page's purpose. Rewrite the argument when the focus is wrong. Adding a more polished headline cannot repair body content that explains a different point.

For a self-contained deck, the visible page must carry the relationships needed to understand its claim. A presenter, speaker notes or the Agent's project knowledge cannot supply missing meaning. This calls for selective explanation, not maximum text. Give research a specific role and keep attribution beside the claim it supports. Carry necessary conditions in the mechanism and retain detailed research limitations in the working evidence. A peer company's reported result remains that company's result throughout design and reconstruction.

When an adjacent industry precedent supports a new proposition, design their relationship explicitly. The proposed service remains the dominant message. A case may establish willingness, a technical foundation or commercial relevance without being the same product. Ask what product a cold reader would describe from the page alone. If its most prominent evidence makes the proposal look like the precedent, revise the hierarchy or select a narrower evidence anchor. Correct attribution alone cannot prevent this framing error.

Match introductory copy to the page’s argument. A technical feasibility page needs an explicit relationship between established foundations and product-specific engineering, not a generic description of the process underneath. In precedent panels, distinguish official product names, named features and general architectural patterns. Align the explanatory depth and identity treatment of peer columns while preserving their substantive differences. Extra words are useful only when they add missing meaning.

Read each prominent number and its adjacent explanation as one factual sentence. The reader should immediately know what was counted or measured, for whom, over what period and against which denominator when relevant. A technical metric name alone may leave that sentence incomplete for this audience. Supply a plain-language explanation beside the figure while preserving the metric's actual basis. A distance-weighted capacity ratio, for example, must not silently become an unweighted count of flights or seats. Prefer one clear metric and referent. Repeating the same percentage as a headline, bar label and scale annotation needs an additional communication purpose. Source attribution establishes credibility but cannot repair an unexplained number.

When the user requests an intent or content gate, show that narrative and page-level copy and wait for approval before image generation. Reopen the affected gate if later work materially changes the argument. A layout may improve emphasis, but it cannot supply a business explanation that was never authored.

Put the intended wording into the existing slide intent, with exact strings for approved text. Keep content roles identifiable so later edits can refer to a specific title, explanation or label. Pass the complete intent through `prepare_generation.py`.

The compiled brief already asks the image model to preserve exact wording, facts and qualifications. This instruction does not guarantee the model's output. Do not delegate factual claims or final editorial decisions to the image model merely because it can render text.

## After image generation

Inspect both the visual design and the content. Compare the generated text to the authored strings, then read the actual words from the intended reader's perspective. Attractive layout does not excuse unclear or altered meaning.

For an authorised copy-only correction that fits the existing slots, keep the selected image as the composition reference. Record the affected entity, original text, revised text, reason and preserved meaning in the working handoff or a linked copy-revision record. Preserve the original image and generation request as evidence of what was generated.

Update the intent's wording and the handoff's independent content obligations. Use the semantic entity's `authored_text` for the revised native text and keep its source text accurate to the observed image. Do not invent a new field in a strict schema. Keep geometry, typography groups, font targets, assets and visual relationships stable. Re-run the packaged measurement, reconstruction and rendering stages for the affected slide.

The comparison now checks two explicit things. The accepted image governs the design. The recorded revised copy governs the authorised native wording. Do not treat that recorded text difference as an unexplained reconstruction defect or refresh old hashes to imply the image contained it.

If the correction changes the argument, data, required content, visual relationships or composition, revisit the affected upstream decisions. If text is inseparable from raster artwork, use the normal image-edit or reconstruction workflow. The native-copy exception is not a route around the reconstruction contract.

## Existing editable PowerPoint

When a user supplies a newer native file, it supersedes older constructor scenes for subsequent edits. Inspect the supplied slide, preserve its frame and design, and record its baseline. Apply authorised changes to the identified native text objects through the supported editing path. This does not authorise a custom replacement deck builder or re-creation of the whole slide.

The companion should keep approximately the same wording footprint. If revised copy no longer fits, first rephrase while retaining the meaning. Do not silently reduce font size or move the layout. Surface the specific conflict if a meaningful fit needs a new design choice.

## Verification

Render and inspect the edited slide for comprehension, line wrapping, peer balance, clipping and metric associations. Check that the intended objects alone changed. A fitting report or matching word count is supporting evidence, not proof of layout preservation. When only wording suggestions are requested, return the copy without editing the presentation.

## Count-only architecture framing and action-only value copy

An architecture claim should identify its consequential components or design relationship and the work they enable. A count such as three services cannot carry that meaning alone. On a value page, connect policy or governance actions to their practical purpose. The reader should see why the action matters without having to infer the economics or operating consequence. Preserve the real relationship instead of attaching a generic benefit word.
