# The SlidePoise project showcase

A static, self-contained product page for creating editable presentations with Codex. It uses system fonts, plain HTML, CSS, and JavaScript. It has no application framework, analytics, remote font requests, or build dependency.

From the repository root, run

```bash
python -m http.server 8000
```

Open [the project page](http://localhost:8000/docs/site/). Use HTTP so the browser can load the example manifests. Opening `index.html` directly through a `file` URL does not provide the required fetch access.

The Samples module combines visible presentation previews and the slide viewer in one container. Each preview shows the case title and smaller style metadata. Selecting a sample updates the adjacent viewer and its retained evidence. The strategy scenario is illustrative. The essay explores a personal approach to working with AI. The Plan row reads the original outline’s throughline. Its detail view shows the audience, argument and complete structured content for the selected page. Thumbnail navigation changes the plan details while keeping the dialog open. A separate Show slide action opens the corresponding finished slide.

The viewer provides Editable PowerPoint, Compare, and AI-generated design modes in one canvas. In Editable PowerPoint mode, click a native object or focus the slide and use arrow keys to inspect its text, type, geometry, and chart data. The Editable objects button opens the layer list. This is a read-only inspection of the real PowerPoint objects.

Expand opens a page dialog containing the same live viewer. Slide selection, object inspection and the comparison position carry over. Close or Escape returns it to its original position, restores the page's scroll position, and returns focus to the Expand button. This works within the browser page and does not invoke operating-system fullscreen.

The generated design can be enlarged directly from its canvas. Whole content cards open the brief, images and chart evidence in a page dialog. Pointer feedback changes the card surface and subtly scales its image. A short scale and fade uses the source card’s position when the dialog opens and closes. Ordinary content cards use their whole surface for interaction, without repeated floating expand icons. Keyboard and reduced-motion actions are immediate. General source JSON is presented as readable fields and expandable sections. The presentation plan and slide brief have dedicated content renderers. Exact initial, revision and historical prompts appear only in technical disclosures, with the original source unchanged. Escape closes the dialog and returns focus. The only public download action is the sample PowerPoint, beside its description below the viewer. PDF and source archives remain in the underlying example directories.

The How it works section follows one actual opportunity slide. First, a compact preview of its authored intent sits beside the generated content image. The opened slide plan includes every required content item, with actual tables, formulas, arguments, decisions, assumptions and relationships. Repeated planning notes and design rules remain expandable. Next, the same chart region appears as a chart interpretation, an OpenCV measurement overlay and the actual native PowerPoint render. The interpretation preview is a cropped excerpt from the authored reconstruction highlights. It does not claim to be the complete source semantic map. Full native object coverage is available in the sample inspector. The chart's categories and values agree across the intent, semantic map and extracted native object. Selecting the PowerPoint chart card opens that slide and selects the corresponding chart after its object document has loaded. A later sample or slide selection cancels that navigation's selection effect.

Plan, Design, Reconstruct and Review are the shared presentation stages. Each stage has an actual image preview or a document icon and a named disclosure control. Expanding it reveals the selected sample's artifact titles, thumbnails and file types. Longer explanations stay in the individual artifact dialog. Artifact counts do not change the number of stages. The stages explain the work and allow revisions to return to earlier decisions. They do not represent an enforced runtime state machine.

Setup states the verified Codex environment and local prerequisites, with one copyable installer command. OpenCV supplies the measurement route. LibreOffice and Poppler are separately installed for the local preview route.

The current presentation, slide, and viewing mode are reflected in the URL. Copy a link such as `?deck=personal-thinking-system&slide=s04-trace&view=compare#studio` to share a specific comparison. Unknown identifiers fall back to the first available presentation or slide.

## Build a portable copy

```bash
python docs/site/build.py --check
python docs/site/build.py --output /tmp/slidepoise-showcase
python -m http.server 8000 --directory /tmp/slidepoise-showcase
```

The builder validates every referenced artifact, copies the page and complete example directories, and creates a checksum inventory. Open `/docs/site/` in the resulting bundle. The root page also links to the showcase. No deployment is performed.

For a personal website, copy the bundle at a path where `docs/site/` and `examples/` retain their relative positions. Its pages and assets also work behind a URL prefix. The browser requires all eight declared site files, including the planning and object-inspection modules. The [asset guide](../SHOWCASE_ASSETS.md) documents the source contract and capture material.

## Maintain the page

`showcases.json` contains relative manifest paths, explicit artifact assignments for the four workflow stages and the source bindings for the concrete walkthrough. Each example manifest owns its presentation content, assets and process evidence. The builder checks that every process artifact appears exactly once in the stage mapping and that the walkthrough follows the same chart data and target image throughout. The page loads the index, manifests and outlines first. It loads selected slide plans, technical prompt disclosures, images and object records as needed. Full artifact integrity checks belong to the builder. A failed image or artifact preview has an explicit error state.

The index’s `brief_sources` assigns a retained planning outline to each sample. `planning_inputs` explicitly declares every slide intent and its image-generation inputs. The builder checks matching slide messages, complete content, source files and recorded prompt hashes. The page distinguishes consulting initial requests and revision inputs from the editorial sample’s retained historical prompts. It does not label an initial request as the final accepted image call. The index also provides `artifact_labels` and `presentation_summaries` for concise public copy. Artifact labels use exact process paths and must name every retained process file. This keeps interface wording separate from the verified production manifests and their hashes. Initial fragment navigation waits for dynamic content to establish its layout and is cancelled after any user interaction or subsequent navigation.

The reveal control uses a native range input, with arrow-key control and an accessible current value. Slide and evidence controls use ordinary buttons. After a later plan-page selection, only the dialog content container scrolls if needed to keep the new page heading visible. The background position and navigation focus stay intact. Initial opening preserves the plan overview. Both sample previews remain visible on narrow screens, the thumbnail rail becomes horizontal, and the object panel moves below the slide. Pointer navigation scrolls smoothly to its section. Keyboard actions are immediate, and reduced motion disables movement. The copy button selects the command if clipboard access is unavailable.

An optional manifest `canvas` describes the full slide dimensions and the generated content region in pixels. AI-generated design and Compare place the original generated image in that region on a white slide canvas. The shared frame is left blank in the target and is visible in the actual PowerPoint render. Without `canvas`, the target fills the slide. The builder rejects nonfinite dimensions, empty regions and regions outside the full slide.

## Native object inspection

`object-inspector.mjs` places normalized object polygons over the actual PowerPoint render. `extract_objects.py` reads the delivered PowerPoint XML, including its group transforms, native text, chart relationships, and slide order. It writes one object record per slide and updates the manifest's optional `objects` path.

Browser object identities use page and traversal order within the bound PowerPoint file. The source `native_id` is preserved separately. This keeps each visible object selectable even if a source package reused a native ID for a shape and a table. The builder rejects duplicate browser identities.

After replacing or rebuilding a presentation, export its object records again.

```bash
python docs/site/extract_objects.py --manifest examples/consulting-ai-transformation/showcase.json
python docs/site/extract_objects.py --manifest examples/personal-thinking-system/showcase.json
python docs/site/build.py --check
```

The builder rejects stale records. Each record must match the slide id and page number, the declared PowerPoint path and SHA-256 hash, and the rendered image path and SHA-256 hash. A changed deliverable or reordered slide requires a fresh extraction before packaging.

The surface element must fit the rendered slide's full 16:9 rectangle. The current layout keeps that rectangle intact as the side panel opens and as the viewport changes. Object coordinates use percentages of the same rectangle.

The module interface is `createObjectInspector({surface, panel, announce, onSelectionChange, onStateChange})`. The returned inspector supports `load(url)`, `select(id, options)`, `setEnabled(boolean)`, `clear()`, and `destroy()`. `load` returns a promise. `select` delegates to the existing selection behavior and returns whether an object in the current document was selected. Its optional `focusCanvas` flag moves keyboard focus to the selected object canvas. The page owns panel visibility. It opens the panel on selection and disables object interaction outside Editable PowerPoint mode.

Run the manifest check after updating an example. For UI changes, inspect desktop and mobile layouts, navigate with the keyboard, compare both slider endpoints, switch decks and process artifacts, and verify actual downloads. File validation does not establish visual quality.

The portable bundle boundary has focused tests for complete evidence retention, checksums, missing renders, path containment, duplicate slide identities, preservation of an existing output directory, stale object records after changes to the PowerPoint, render or page order, complete workflow assignment, presentation outline binding, and the walkthrough's agreement with its actual source artifacts.

```bash
PYTHONDONTWRITEBYTECODE=1 python docs/site/test_build.py
node --check docs/site/app.mjs
node --test docs/site/planning.test.mjs
```

The sample viewer also exposes the retained interpretation and OpenCV measurements for every page. Element groups renders all authored object allocations and lets visitors highlight recorded groups. OpenCV measurements uses the actual debug overlay and visible-ink bounding boxes. Selecting an element shows its source-image coordinates, size and recorded colour or line count. Late responses are cancelled when the visitor changes slide or mode. These records describe the reconstruction work, and do not establish a pixel-perfect match.

The Console section embeds a sandboxed copy of the real Console UI with an in-memory API adapter and bundled sample assets. A Tap to interact / Done gate controls scrolling on desktop and mobile. No API request reaches an installed Console, and reloading resets the demonstration. The opening command beside the demo launches the installed local Console. `build_console_demo.py` refreshes the bundled UI and sample records from an isolated Console on port 8766.
