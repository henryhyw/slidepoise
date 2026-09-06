# Selective illustration refinement

Read `raster-composition.md` before selecting sources. A generated raster is eligible for consideration when it is neither a canonical asset nor faithfully reconstructable native geometry. Eligibility alone does not justify regeneration.

Inspect original crops at intended output scale and review relevant details. Record an explicit `raster_decision` for each meaningful novel illustration. Reuse sharp, sufficiently resolved originals. Select `refine` only for a visible problem worth editing. Keep intrinsic lettering inside its raster owner. Handle overlapping editable text through the clean-plate route.

## Selected source board

Run `scripts/prepare_illustration_refinement.py` after those decisions. Only entities selected for `refine` enter the board. Others retain their original sources. The borderless model-input board contains no added labels. A separate labeled review board supports visual inspection. Board enlargement is a presentation aid and does not prove that source detail has improved.

Ask the user when the focused edit adds a material cost or identity choice that was not already authorized. Otherwise the Agent may make one focused edit, inspect it, and record the affected entity IDs. Reusing original crops needs no extra checkpoint.

## Focused edit and extraction

Send the selected source board and brief to the host image editor. Preserve subject, intrinsic lettering, aspect ratio, arrangement, and local appearance. Do not add external labels or merge slots. The edit may repair small generation defects, so it must be inspected as a new asset.

Run `scripts/extract_refined_illustrations.py` to crop known slots. Visually compare each returned asset with its original at intended output scale before applying it. If rejected, keep the original and update its decision. Do not silently spend another call.

Run `scripts/apply_illustration_sources.py` only for visually selected items. It attaches `raster_source_override` without changing the measured placement. Inspect the reconstructed result for changed intrinsic text, lost grain, halos, color drift, crop edges, and residual foreground text.

Clean plates use the original panel or full-canvas coordinate system and targeted image editing. Do not send them through the isolated refinement-board path.
