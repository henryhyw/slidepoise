# SlidePoise showcase production plan

The two retained presentations are now documented in [the production record](SHOWCASE_PRODUCTION.md). This file preserves reusable test prompts and a proposed filming outline. Its fresh-chat and screen-recording steps describe future replay material.

## Purpose

Validate the automatic five-slide workflow in a fresh Codex chat, preserve evidence for debugging, and collect authentic material for the public launch video.

Run the Consulting deck first. Fix any product defect before running the Personal Website deck.

## Test A

Use a fresh Codex chat and paste this prompt.

```text
$slidepoise

Create a fully automatic five-slide editable PowerPoint presentation.

The topic is "How a professional services firm can move from scattered AI tools to organization-wide intelligence in 12 months." The audience is the executive leadership team. Help them understand why action is needed now and how investment should be phased.

Use the Consulting Profile for this presentation. Decide the narrative, slide content, evidence structure, layouts, and visual metaphors yourself. Do not wait for per-slide approval. Give me brief progress updates at useful moments and continue working.

Keep creative-call costs restrained. Aim for one strong initial design per slide. Make a targeted repair only when there is a material content, visual, or reconstruction problem. Do not generate batches of candidates merely to explore styles.

Complete the outline, slide-by-slide visual generation, editable reconstruction, deck assembly, and final visual review. Deliver the PPTX, individual slide previews, and a full-deck contact sheet. Briefly identify which regions are native editable objects and which remain raster images. Preserve the run directory and intermediate artifacts for a later product demonstration video.
```

## Test B

Run this only after Test A has completed without a product-blocking defect.

```text
$slidepoise

Create a fully automatic five-slide editable PowerPoint presentation.

The topic is "How I turned AI from a productivity tool into a second thinking system." This is a public talk with a clear personal point of view and an identifiable authorial voice. The audience is knowledge workers interested in AI.

Use the Personal Website Profile only for this presentation. Do not change the global default Profile. Decide the narrative, slide content, layouts, pacing, and visual metaphors yourself. Do not wait for per-slide approval. Give me brief progress updates at useful moments and continue working.

Keep creative-call costs restrained. Aim for one strong initial design per slide. Make a targeted repair only when there is a material content, visual, or reconstruction problem. Do not generate batches of candidates merely to explore styles.

Complete the outline, slide-by-slide visual generation, editable reconstruction, deck assembly, and final visual review. Deliver the PPTX, individual slide previews, and a full-deck contact sheet. Briefly identify which regions are native editable objects and which remain raster images. Preserve the run directory and intermediate artifacts for a later product demonstration video.
```

## Evidence to preserve

- The opening user prompt
- The first visible deck outline
- One representative generation target
- The same slide after editable reconstruction
- The five-slide contact sheet
- The final editable PPTX
- A short screen recording of editing one title
- A short screen recording of moving one object
- A short screen recording of deleting or reordering one slide
- Any failure, recovery, or page-local rerun that demonstrates flexible orchestration

## Product video

Use authentic product footage as the evidence layer. An AI-generated visual can provide a short opening or transition, provided it is not presented as real product operation.

Suggested 40-second sequence

1. 0 to 4 seconds. A polished visual hook built around an idea becoming a deck.
2. 4 to 9 seconds. The real prompt is pasted into a fresh Codex chat.
3. 9 to 16 seconds. The deck outline appears and the Agent continues automatically.
4. 16 to 25 seconds. Five generated slides appear as a fast contact-sheet montage.
5. 25 to 33 seconds. PowerPoint opens and a title and visual object are edited.
6. 33 to 38 seconds. One page is reordered or revised without rebuilding the other pages.
7. 38 to 40 seconds. SlidePoise name and the concise promise appear.

Recommended closing promise

```text
Tell Codex the story. Get an editable deck.
```

## Acceptance questions

- Did the Agent finish without per-slide approval prompts?
- Did it create exactly five active slides in the requested order?
- Could one slide be revised without invalidating unaffected pages?
- Did the final PPTX open normally?
- Were important text, shapes, charts, and connectors editable where faithful reconstruction allowed it?
- Did the contact sheet show a coherent deck with useful layout variation?
- Did the selected Profile remain consistent across the deck?
- Did the second test avoid changing the global Consulting default?
