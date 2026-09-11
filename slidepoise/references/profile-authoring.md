# Guidance profile authoring

A guidance profile is a user-owned, evolving visual system. It holds design guidance, modes, and visual references for one recognizable presentation language. Icon and component assets live in reusable Library Sets that one or more profiles may select. Treat the installed Consulting, Editorial Archive, and Monochrome Modern profiles as useful starting points, not a closed set.

## Agent behavior

When a user describes a desired style, supplies visual references, or asks to evolve a profile, help them do it through normal conversation. Do not require them to understand JSON, catalogs, file locations, schemas, or internal pipeline terminology.

First clarify only the choices that materially affect the result. Infer ordinary metadata from the conversation and supplied visuals. Then create or update the profile and report the user-visible outcome. Explain technical storage or implementation only when asked.

If the user wants to make choices themselves, open the SlidePoise Console with `slidepoise console --view style` or `--view resources`. Style owns every configurable profile choice, including its selected Library Sets. Resources manages the sets and their contents. The Agent and Console edit the same installed profile and catalogs.

## Creating and evolving profiles

Use `slidepoise profile create` to start from the closest installed profile. Choose Consulting for disciplined, information-rich communication. Choose Editorial Archive for tactile collage, paper, typewriter, handwriting, and documentary imagery. Choose Monochrome Modern for flat black, white, and grey blocks, crisp geometry, and editorial typography. A new profile remains fully independent after creation.

Creation copies the source profile's current effective style, including saved font and color changes and references from a configured external location. Subsequent edits to the source do not change the copy.

Use `slidepoise profile update` with the current profile revision for structured changes. Preserve useful prior guidance and user-owned resources. Do not rewrite unrelated fields merely to normalize them.

Add a user-approved visual reference with `slidepoise profile add-resource`. Never silently turn every uploaded run asset into a persistent profile reference. Ask or infer clear intent that it should guide future work.

Create a coherent reusable family with `slidepoise library create icons|components`. Add an icon or component with `slidepoise library add-resource`. Record a useful name, description, semantic tags, source URL, and license or usage permission. Do not create one loose set for every file. Group assets only when they share a defensible source, visual language, or component purpose. Select complete set IDs in the profile's `library_sets` field.

Profile fields may leave palette, typography, density, or icon treatment to Agent judgement. Read `style_agency` before treating a concrete fallback value as a hard instruction. `specified` is a constraint, `guided` is a preference, and `agent_decides` or `agent_decides_from_references` grants visual freedom within the profile's purpose and references.

## Learning a style from references

Inspect every supplied reference at a useful size. Establish which qualities the user wants to carry forward. When that intent is clear, proceed without a questionnaire. Distinguish observed treatment from inferred intent. A screenshot rarely establishes an exact font, reusable grid or brand colour. Mark uncertain matches as proposed choices and verify them in the rendered result.

For each reference, identify the relationships that create its character. Consider the contrast between text roles, tonal emphasis, alignment, spacing, image treatment and the relationship between imagery and information. Record concrete observations in the existing reference catalog description. Include what to borrow and what is incidental, such as its subject, labels, page furniture or a composition suited to one particular message. Keep source and usage information with the image.

Compare references before generalising. Repeated qualities are evidence for a common style, while differences may express a deliberate light/dark variation or different information needs. Repetition alone does not make a rule mandatory. Resolve incompatible directions through the user's intent, a separate mode or a consequential clarification. Do not average incompatible styles or silently inherit unrelated rules from the profile used as a starting point.

Translate the synthesis into the existing profile fields. Put reusable decisions in `visual_principles` and `reasoning_principles`, observable review questions in `review_questions`, and concrete recurring mistakes in `anti_patterns`. Use `design_overrides` for proposed font roles, palette and other supported settings. Use `modes` for coherent variations and `visual_reference_priorities` to retain their source images. Reserve `hard_rules` for genuine constraints. Explain which reference observations support the principles without duplicating an analysis report inside the generation prompt.

Set `style_agency` deliberately. A specified property is a constraint, a guided value allows adaptation, and an Agent-decided value is a fallback. Keep density independently configurable. A spacious reference can teach emphasis and spacing without limiting how much evidence a future slide may carry. Preserve the relationships between text roles and groups as density changes. Do not convert the reference's coordinates, exact chart type or number of blocks into a general layout prescription.

Check the resulting profile for contradictory instructions before using it. Match the proposed font roles and tonal treatment across the style defaults, text reconstruction policies, semantic tokens and hard rules. A mode description does not automatically change those values. When choosing a mode for a presentation, materialise its relevant choices in supported session `design_overrides` and the resource selection's `style_direction`, then resolve the configuration and compile again. Keep unselected modes out of that page's instructions.

Use the guidance on new content whose communication jobs differ from the reference. An actual requested deck can supply this transfer check. Choose representative pages that expose the relevant uncertainties, such as an explanation with directed relationships and a page with detailed evidence. There is no fixed reference count or mandatory extra sample deck. A single reference supports a narrower inference than a varied set.

Inspect generated designs and their native renders against both the reference observations and the new content. Check whether the common identity survives, whether the content remains clear and whether each page chooses an appropriate composition. If a result only repeats the reference layout, revise the over-specific guidance. If a deviation comes from generation or reconstruction, repair that stage without turning the local defect into a universal style rule. Save the useful principles and references through the existing Profile commands. Keep transient experiments and review records in the run, and report any untested variation honestly.

When updating an established profile, preserve explicit user choices and unrelated resources. New guidance applies to future runs. A run used to test the evolving profile adopts each revision explicitly before recompiling its affected generation requests.

## Session and profile boundaries

A run captures profile and global defaults at creation so concurrent sessions remain stable. Session overrides affect only that run. Profile edits become defaults for new runs. Existing runs adopt newer defaults only after an explicit request.

Use a session override for one slide, audience, temporary palette, or exceptional asset. Evolve a profile when the user wants the choice to recur. Create a separate profile when the desired language has a distinct identity that would make the existing profile internally inconsistent.

## User-facing guidance

When a user is unsure how to begin, offer a short path based on their goal. Ask for the message, audience, and any references they already like. Then propose the closest profile or help create one. Keep the conversation about communication and visual intent. Reveal commands, manifests, measurement layers, and reconstruction details only when the user asks how the system works.
