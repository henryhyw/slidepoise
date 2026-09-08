# Autonomous review

SlidePoise assigns routine inspection and correction to the Agent. The published examples show achievable output quality. They do not establish a success rate for new briefs, models or rendering environments.

## What the workflow requires

The Agent reads the rendered deck against the original brief, then compares it with the selected designs. These readings catch different failures. A faithful reconstruction can still preserve a mistake in the generated image. A valid PowerPoint can still omit a relationship or weaken the intended hierarchy.

For decks and complex slides, an independent reviewer inspects the images when the host supports subagents. It receives the intent and current artifacts before seeing the author's acceptance statements. Without subagents, the host performs a separate inspection pass. Findings stay open until the Agent has corrected the relevant inputs and inspected a fresh render, or supplied concrete evidence for rejecting the finding. Shared changes receive another cross-page review.

The normal preview commands expose native table-text discrepancies from the actual PDF. The release collector checks that the inspected render belongs to the supplied PowerPoint and page. Missing extraction remains an explicit limitation. These tools supply evidence and provenance. They cannot judge whether the content inventory is complete or the presentation communicates well.

## Independent detection exercise

On September 8, 2026, a separate reviewer received three anonymized cases. Each contained only the slide intent, generated design and PowerPoint image. It read the packaged review guidance and opened all six images. It was instructed to identify material and important problems without assuming every case was defective. It received no expected findings, repair history or previous acceptance statements.

| Case | Retained source | Independent findings |
| --- | --- | --- |
| A | Consulting operating-model page at `2a113dc` | Both return connectors were missing from the PowerPoint. One source-design return path also lacked clear direction. Supporting text had lost prominence and the table alignment had changed. |
| B | Consulting investment-decision page at `2a113dc` | Adoption and Downside broke across lines. Formula labels became crowded and lost their association with individual inputs. Supporting-text hierarchy weakened. |
| C | Editorial closing page at `e238c36` | No material or important visual issue. The reviewer distinguished minor type differences from losses that required revision. |

These inputs remain retrievable from the repository history under `examples/<case>/run/slides/<slide-id>/`. The inspected files were `work/slide-intent.json`, `work/accepted-slide.png` and `deliverables/render.png`. The slide IDs were `s03-operating-model`, `s05-investment-decision` and `s05-close` respectively.

The host checked the findings against the known defects. The exercise demonstrated independent detection in two historical failure cases and appropriate restraint on one satisfactory control. It did not test an autonomous correction run or generation from an unfamiliar brief. Three selected cases cannot establish a general success rate.

## Runtime verification

The ordinary single-slide preview command rendered the historical investment PowerPoint again and examined 38 native table cells. It reported the two broken words. The same command rendered the corrected PowerPoint and examined the same 38 cells with zero discrepancies. The host opened both new images and confirmed the reported difference.

Regression tests cover changed PowerPoint bytes, substituted preview images, a wrong page number, missing render provenance, modified text evidence and diagnostics scoped to the selected page. Unavailable extraction produces an unavailable result with no discrepancy count. The full Python suite passed with 299 tests.

## Remaining evidence needed

Before claiming dependable unattended performance across new work, evaluate fresh briefs through planning, generation, reconstruction, correction and final review without supplying expected fixes. Include unfamiliar content, dense charts and tables, branching relationships, artwork, different scripts, aspect ratios and font environments. Preserve failed attempts as well as final outputs. Record user interventions, unresolved defects, correction rounds and resource use, and have an independent reader assess the delivered decks.

Run that evaluation again when the host model, image model, skill or renderer changes. The present evidence supports the specific detection and provenance improvements above. It does not support a promise of flawless output on every run.
