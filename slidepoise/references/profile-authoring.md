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

Visual references provide visual and compositional evidence. Describe what should be learned from each reference, including hierarchy, typography, density, material, image treatment, and restraint. Avoid copying its content. When a reference conflicts with the existing profile, discuss whether it represents a new mode, a profile-wide evolution, or a one-run override.

## Session and profile boundaries

A run captures profile and global defaults at creation so concurrent sessions remain stable. Session overrides affect only that run. Profile edits become defaults for new runs. Existing runs adopt newer defaults only after an explicit request.

Use a session override for one slide, audience, temporary palette, or exceptional asset. Evolve a profile when the user wants the choice to recur. Create a separate profile when the desired language has a distinct identity that would make the existing profile internally inconsistent.

## User-facing guidance

When a user is unsure how to begin, offer a short path based on their goal. Ask for the message, audience, and any references they already like. Then propose the closest profile or help create one. Keep the conversation about communication and visual intent. Reveal commands, manifests, measurement layers, and reconstruction details only when the user asks how the system works.
