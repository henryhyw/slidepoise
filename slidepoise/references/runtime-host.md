# Host runtime adapter

SlidePoise owns orchestration; the host supplies image generation/editing, visual inspection, file execution, and rendering.

## ChatGPT chat
- Use ChatGPT's native image-generation/edit capability for the creative target and targeted edits.
- Pass the generation context sheet plus any separately required reference images exactly as the generation brief requests.
- Use `slidepoise_runtime.py reconstruct-slide` and the packaged scene renderer for deterministic measurement and reconstruction. PptxGenJS runs behind this boundary.

## Codex
- Keep the SlidePoise parent agent as the orchestrator.
- Use the available image-generation skill/tool for generation and edits. If the Codex host exposes image-capable agent delegation, delegate only that bounded image call and return the image/result to the parent SlidePoise workflow.
- Do not assume a particular subagent API name. Adapt to the host's current image-generation interface.
- Use `slidepoise_runtime.py reconstruct-slide` and the packaged scene renderer. Do not create or invoke a direct PptxGenJS deck builder for a presentation run.

## Measurement

OpenCV supplies the complete measurement path. Setup installs its runtime dependencies without downloading a segmentation model.

The internal SAM adapter remains readable for existing explicitly configured runs. It is experimental, disabled by default and has no managed installer or Console control. Do not enable or advertise it as part of a normal run. For a deliberately configured experiment, the host must assign an eligible semantic entity, inspect the returned candidates and select a `sam_candidate_index` before a mask contributes. Its execution and selected masks remain in the measurement JSON. A generated candidate without a host selection is not a contribution. The host retains semantic and visual authority.

## Common rule
The configured image model is a preference, not an architectural dependency. If the host cannot generate/edit images, stop at that stage rather than replacing the creative image stage with Python drawing, HTML/SVG composition, or a fixed template.

The same rule applies after generation. If semantic mapping, OpenCV measurement, contract compilation, or scene rendering cannot complete, stop with the exact blocker. Do not improvise an alternate reconstruction path.
