# SlidePoise product requirements audit

This audit records the simplified product boundary introduced for deck-scale creation.

| Requirement | State | Evidence |
|---|---|---|
| One skill handles one slide or a complete deck | Complete | `slidepoise/SKILL.md` infers scope from user intent and uses one deck model for every request. |
| The deck outline stays editable during production | Complete | `references/deck-orchestration.md` defines stable slide IDs, ordered active entries, scoped invalidation, and add, remove, reorder, split, and merge behavior. |
| Every slide keeps an isolated workspace | Complete | New runs contain `slides/`. Page-local generation, mapping, measurement, and reconstruction artifacts live beneath stable slide IDs. |
| Editable scenes assemble into one ordered PPTX | Complete | `slidepoise_runtime.py render-deck` resolves a deck scene manifest. The Node runtime accepts multiple scenes and writes them in manifest order. |
| Parallel page work is optional | Complete | Independent page workers can own isolated slide folders. Sequential parent-Agent execution remains valid when subagents are unavailable. |
| User checkpoints adapt to intent | Complete | Plan, style, sample, image, and illustration checkpoints are optional tools. Fully automatic requests can continue after Agent review. |
| Deterministic logic reports objective facts only | Complete | Structural errors may block construction. Font size, density, balance, similarity, and visual acceptance remain host-Agent decisions. |
| OpenCV provides the complete measurement route | Complete | OpenCV measures object boundaries, crops, colours, and contours without downloading a segmentation model. |
| Session Panel is lightweight | Complete | The run-bound panel only exposes current-presentation style, Library Set, and asset overrides. It has no stages, approvals, progress, previews, downloads, versions, picker, or project controls. |
| Console is global | Complete | Console exposes reusable Profiles, Profile references, Library Sets, and local capabilities. Presentation lists and run-detail views are absent. |
| Profile and resource isolation is preserved | Complete | Reusable visual guidance remains external to the skill. Session overrides never mutate their parent Profile. |
| Existing run history stays recoverable | Complete | Legacy run files remain readable. Structural edits preserve page folders and archive omitted work instead of deleting evidence. |

## External skill comparison

The review of `ningzimu/image-to-editable-ppt-skill` and its companion `codex-ppt-skill` found four transferable ideas.

- Normalize deck work into an ordered page manifest.
- Give each page an isolated workspace and stable ownership boundary.
- Allow independent pages to run concurrently.
- Assemble final pages from recorded page artifacts in explicit order.

SlidePoise adopts those structural ideas. It does not adopt their hard single-page versus multi-page branching, mandatory worker availability, page `passed: true` quality gate, fixed sample approval sequence, or user-visible project state machine. Those mechanisms solve orchestration through deterministic enforcement. SlidePoise keeps orchestration inspectable while leaving narrative, visual, and interaction decisions with the Agent.

## Verification

Release checks include skill validation, configuration and catalog preflight, stable boundary audit, Python tests, frontend tests, Node syntax checks, distribution builds, and a real two-page PPTX assembly test. Visual behavior changes still require representative rendered inspection when a concrete slide is available.
