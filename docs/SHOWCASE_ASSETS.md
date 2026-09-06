# Showcase assets and production evidence

The project showcase is built from two real SlidePoise runs. Each curated example is self-contained and keeps the generated design, editable reconstruction, source evidence, and final deliverables together.

| Example | Purpose | Source manifest |
| --- | --- | --- |
| Consulting | An illustrative executive narrative about an AI operating model | [`consulting-ai-transformation/showcase.json`](../examples/consulting-ai-transformation/showcase.json) |
| Editorial | An authored essay about AI as a second thinking system | [`personal-thinking-system/showcase.json`](../examples/personal-thinking-system/showcase.json) |

The [static project page](site/README.md) reads these manifests directly. The sample chooser and slide viewer share one container, with each case title above its style metadata. The viewer keeps Editable PowerPoint, Compare, and AI-generated design modes in one canvas and lets visitors select objects extracted from the actual PowerPoint. Images and production evidence open inside the page. The inspection is read-only.

## Portable manifest

All artifact paths are relative to the manifest directory and remain inside that example. URLs, absolute filesystem paths, and parent-directory escapes are excluded from the public asset contract.

```json
{
  "schema_version": 1,
  "id": "example-id",
  "label": "Consulting",
  "title": "A presentation title",
  "subtitle": "A five-slide executive narrative",
  "style": "Consulting Profile",
  "summary": "What the presentation helps its audience understand.",
  "note": "The business scenario and figures are illustrative.",
  "slides": [
    {
      "id": "slide-01",
      "title": "The slide’s communication job",
      "claim": "A short accessible description of its main message.",
      "target": "assets/slide-01-target.png",
      "render": "assets/slide-01-render.png",
      "thumbnail": "assets/slide-01-render.png",
      "scene": "run/slides/slide-01/work/reconstruction/constructor-scene.json",
      "evidence": "assets/slide-01-semantic.png",
      "objects": "assets/slide-01-objects.json"
    }
  ],
  "downloads": {
    "pptx": "deliverables/presentation.pptx",
    "pdf": "deliverables/presentation.pdf",
    "bundle": "deliverables/source-bundle.zip"
  },
  "process": [
    {
      "title": "Shape the narrative",
      "description": "The retained outline records the audience and the job of every slide.",
      "artifact": "run/work/deck-outline.json"
    }
  ]
}
```

`target` and `render` are required for every slide. `thumbnail`, `scene`, `evidence`, and `objects` are optional. The native object inspector uses the complete geometry extracted from the delivered PowerPoint. The optional `evidence` image is a curated reconstruction highlights image. It is not the complete semantic map. Each public example includes an editable PowerPoint download and at least one retained process artifact. PDF and a portable source bundle are optional retained assets. The public page offers only the PowerPoint download and keeps image and source previews inside the page. Titles and descriptions are authored explanations, with no computed quality rating.

For body-only generated targets, an optional deck-level `canvas` records `full_slide_px` as `[width, height]` and `content_region_px` as `[left, top, width, height]`. For example, a `[1920, 1080]` slide with `[0, 64, 1920, 960]` content places its generated 2:1 image below the shared header region. AI-generated design and Compare preserve that placement on a white full-slide canvas. They do not synthesize a generated header or footer. Omit `canvas` for a full-slide target. The builder checks positive finite dimensions and containment.

The site builder checks each declared path before creating a bundle. The bundle preserves both complete example directories and adds `asset-inventory.json` with SHA-256 hashes. It reports missing files as a packaging error. These checks establish artifact integrity, not visual quality.

## Website explanation sources

The site index in `docs/site/showcases.json` keeps presentation examples separate from the shared product workflow. Its `workflow` object maps each example id to four lists named `plan`, `design`, `reconstruct` and `review`. Each list contains artifact paths already declared in that example's `process` array. Every retained artifact must appear exactly once. The website displays four stages and expands these lists as sample evidence.

The index’s `brief_sources` binds each sample’s Plan row to its retained planning outline. The plan dialog shows the audience, throughline and complete structured content for its selected page. Thumbnails switch plan pages without closing the dialog. A separate action opens the finished slide. Supporting planning notes and repeated visual rules are expandable.

The index’s `planning_inputs` maps each sample and slide to its complete intent file and explicitly labelled generation inputs. Initial and revision requests retain their original JSON prompts and hashes. Editorial prompts are labelled historical inputs, reflecting the evidence available in that run. These files are validated, copied with the example and checked through actual HTTP responses.

The index's `walkthrough` object selects one example, slide and chart entity. It also points to the actual slide intent, semantic map, measurement JSON and measurement overlay. These paths remain inside the chosen example. The walkthrough uses the manifest's generated target, semantic explanation and extracted native object, plus its actual PowerPoint render.

The builder checks that the same chart exists in all four sources, that its categories and values agree, and that the semantic map's target hash matches the published target image. Crops are computed from authored geometry and actual object polygons. The page does not invent an intermediate render or redraw the chart to suggest closer reconstruction.

## Object records

Run `docs/site/extract_objects.py --manifest <path>` after the final PowerPoint and render images are ready. The exporter reads native PowerPoint objects and writes their normalized geometry, types, text, and available chart data. It includes group transforms and keeps the delivered slide order.

Each object document records `slide_id`, `page_number`, and `source` bindings for the PowerPoint and rendered image. Each binding contains the example-relative path and SHA-256 hash. The builder requires exact agreement with the corresponding manifest paths, files, and slide order. Replacing the PowerPoint, changing a render, or reordering slides requires new object exports before a portable site can be built.

The public viewer fits these selection regions to the full 16:9 rendered image. Selecting an object opens its details without changing the presentation. Text in a preserved image region remains part of that image. The browser does not infer additional editable text from raster artwork.

## Reuse on a project page

Use full-resolution renders for slide galleries. Use the generated target and reconstructed render as a matched pair when explaining reconstruction. A reconstruction highlights image explains selected ownership decisions. Label it as an excerpt. The complete source map and measurement records remain in each run, while native object records describe the final PowerPoint coordinate system.

Keep the consulting scenario’s illustrative-data note wherever its business claims are shown. Keep the personal essay’s authored-demo note wherever first-person statements could be mistaken for a factual biography. Preserve original image provenance and relevant asset licenses alongside reused assets.

## Product footage

The saved slides, images, and source files are ready for a website or an edited video. A truthful video can move from the narrative outline to a generated target, then its measurement evidence, and finally the reconstructed deck.

Real application footage is needed to demonstrate typing a prompt, editing a title, moving a native shape, or reordering slides in PowerPoint. The static comparison page does not prove those interactions. Capture those operations from the actual application and keep the original recording alongside the edit. Label any illustrative animation used between them.

The [production plan](SHOWCASE_PRODUCTION_PLAN.md) contains a suggested video sequence and the original demonstration briefs.
