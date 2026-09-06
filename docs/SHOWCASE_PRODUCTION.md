# Showcase production record

The showcase contains two five-slide presentations built with the packaged SlidePoise runtime. Consulting develops an evidence-based decision about an AI pilot. Editorial presents an authored essay about thinking with AI. Both cases retain the argument, image-generation work, semantic interpretation, OpenCV measurements and actual PowerPoint renders.

The current Consulting revision separates generated content from the inherited PowerPoint frame and includes a dedicated review across all five pages. The Editorial revision preserves its artwork, substantive text and individual compositions while calibrating the recurring Field Notes identity. The [production plan](SHOWCASE_PRODUCTION_PLAN.md) remains a reusable brief and video outline.

## The presentations

| Case | Communication job | Editable structure | Raster regions |
| --- | --- | --- | --- |
| [Consulting](../examples/consulting-ai-transformation/) | Approve a bounded research pilot and release further investment against evidence | 111 text boxes, seven tables with 130 cells, one workbook-linked chart and native presentation geometry | None |
| [Editorial](../examples/personal-thinking-system/) | Keep questions, connections and judgement visible when working with AI | 46 native text boxes plus shapes and editable rules | Eight photographic collages and notebook regions |

Northstar Advisory and the financial quantities are illustrative. The Editorial first-person voice belongs to the sample and does not claim the user's biography. Presentation-specific overrides supplied the style direction without changing the user's installed default Profile.

## Content, frame and cross-page calibration

For Consulting, the full slide is 1920 by 1080 pixels. A 64-pixel header and 56-pixel footer leave a 1920 by 960 content region. The image requests use that 2:1 content canvas and exclude company chrome, page numbers and shared frame rules. Reconstruction places the content below the header. PowerPoint supplies the shared header and footer through its inherited layout.

Each image call has one compiled request, with the prompt, reference-image order and source bindings retained. Focused edit requests preserve their base request and record the correction. The original returned images and normalized accepted targets remain available. The saved Editorial prompts belong to its earlier production run.

The Agent compared the actual Consulting pages together after local page review. This exposed drifting title and subtitle positions, changing decision-message columns and an undersized gate annotation group. The page maps were corrected, then compiled and rendered again. The final pages share Georgia 64px titles, Arial 32px subtitles, 28px supporting and decision text, and 24px table text. The decision band keeps one label column, one message column and an 8-pixel orange accent. Larger opening KPIs are an intentional display role.

The [deck review](../examples/consulting-ai-transformation/run/work/deck-review.json) records the visible comparisons, corrections and remaining font differences. Native structure and source hashes support that review. They do not decide visual quality.

Editorial exposed a smaller recurring role that the earlier page-local reviews had missed. `FIELD NOTES / 01` through `05` used two typefaces, different physical sizes and weights, and wide tracking on the final page. The Agent recognized the shared publication function despite different entity names. The [shared design](../examples/personal-thinking-system/run/work/deck-design.json) maps those aliases to one Andale Mono regular 12 pt role with zero tracking, dark ink and a common lower-left baseline. The cover-only rule and essay descriptor move together as an explicit companion exception.

The revised semantic styles implement that decision, and each handoff binds the shared design by hash. All five pages were measured, compiled and rendered again. The [actual folio comparison](../examples/personal-thinking-system/run/work/folio-calibration/folio-comparison.png) shows the change. Native media payloads and all non-folio text typography stayed unchanged. Same-DPI image comparison found no changed pixels outside the authorized folio and cover-companion regions. Both the page Agent and root Agent inspected the full-page results.

## Retained process

Each example preserves its outline, source assumptions, generated targets, semantic maps and handoffs, OpenCV measurements and overlays, reconstruction contracts, constructor scenes, PowerPoint output and actual renders. Significant page iterations retain the earlier artifacts and the reason for correction. File hashes bind review observations to the files that were inspected.

`assets/` holds stable website-facing targets, renders, semantic explanations and contact sheets. `showcase.json` connects them to the [project page](site/README.md). `deliverables/` retains PowerPoint, PDF and a portable source ZIP. The ZIP carries renderable scenes and required regional images. The full authoring evidence remains in `run/` and in the portable website bundle.

Semantic explanation images show a concise selection of host-authored groups. Their adjacent records point to the complete maps. They explain ownership without claiming automated semantic discovery.

## Reproduce and inspect

From a checkout with development and runtime dependencies installed, use a new output directory.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python examples/rebuild.py \
  examples/consulting-ai-transformation --output-dir output/rebuilt-consulting

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python examples/rebuild.py \
  examples/personal-thinking-system --output-dir output/rebuilt-editorial
```

This repeats measurement, contract construction, compilation, assembly and preview from retained creative inputs. It makes no new image-generation call. `--no-preview` allows native construction when LibreOffice and Poppler are unavailable. Visual acceptance still requires inspection of an actual render.

For a portable source ZIP, extract it into a new directory and follow [portable artifacts](../slidepoise/references/portable-artifacts.md). Run `verify-bundle` before rendering and write new output outside the extracted bundle.

The cases retain their verification in `run/work/rebuild-verification.json`. The current Consulting case was rebuilt from its accepted targets, semantic maps and handoffs in an isolated home. All five 160 DPI previews preserved their pixels. Nine native slide, layout, master and chart XML parts matched. Speaker-note text matched, while the source references correctly changed to the new workspace.

The revised Editorial case also passed a complete isolated rebuild from its targets and maps. All five 120 DPI previews preserved their pixels, and seven native slide, layout and master XML parts matched. Its portable scenes then rendered identically after all eight original temporary crop paths were gone. Each shared-design handoff reference still resolved to the copied file with the correct hash after relocation. These results describe the recorded runtime and fonts, not every Office reader. The [repository verification](VERIFICATION_2026-09-05.json) records the accompanying code and packaging checks.

A separate [native editing proof](../examples/consulting-ai-transformation/run/work/native-edit-proof/) edits an existing title and changes the research chart value from 1,944 to 1,620 in a copy of the assembled PowerPoint. The actual render shows the shorter bar and its updated native label. The other four pages preserve their pixels. The official scenario and separate assumption tables remain unchanged. This demonstrates native editing and workbook-linked labels without claiming that unrelated business calculations update automatically.

## Rendering and reuse

The Consulting deck was reviewed as one five-page LibreOffice render at 160 DPI, with page numbers advancing from 1 to 5. Both samples use discovered macOS fonts. Consulting uses Georgia and Arial. Editorial uses Bodoni 72, Arial, Andale Mono and declared italic interpretations. Font binaries are not distributed. Image-generated lettering and native fonts have different glyph outlines and can wrap differently.

The Editorial photographs and depicted marks come from its retained generated targets. These are historical full-slide designs, including the earlier inconsistent folios. The authorized native calibration made no new image-generation call. Its authored artwork regions remain raster while the surrounding presentation text stays native. Future generated designs follow the current body-only and inherited-frame policy. The Consulting chart retains its numeric data and native labels. Its feedback routes are editable freeforms. Automatic reattachment when moving related objects is not claimed.

The project page shows both sample previews, compares generated content with reconstructed output, and lets visitors inspect real native objects. Images and process evidence open within the page. PowerPoint is the only public download action. The retained PDF and source ZIP files remain available in the repository assets.

The portable site includes a checksum inventory and needs no application framework or remote service. A direct editing demonstration still requires screen recording from PowerPoint itself.
