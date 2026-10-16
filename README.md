# SlidePoise

**Open-source agentic slide generation**

Create editable PowerPoint presentations with an AI Agent. SlidePoise uses image generation to explore compositions beyond fixed templates, then rebuilds the chosen designs as editable text, charts, tables and shapes. You can develop a single slide or a complete deck through conversation.

[Project website](https://slidepoise.github.io/) · [Get started](#get-started) · [How it works](#how-it-works) · [Usage guide](docs/USAGE.md)

https://github.com/user-attachments/assets/90c5ae93-0bc8-4cda-985f-79abf6c67f1f

## Work with SlidePoise

Share your brief, source material and preferred style with your Agent. You can review a sample design before it completes the deck, or let it work through the presentation and give feedback afterwards.

| Stage | What you contribute | What the Agent does |
| --- | --- | --- |
| Content planning | Audience, purpose, evidence and required messages | Develops the argument and slide sequence |
| Visual design | Brand assets, style preferences and feedback | Selects references and assets, prepares a contact sheet, then generates and reviews slide images |
| Reconstruction | Feedback on content or design as needed | Interprets the image, measures objects with OpenCV and builds editable PowerPoint slides |
| Review | Changes you want in the finished presentation | Inspects the rendered deck, corrects differences and delivers the editable file |

The Agent can revisit any stage when your feedback changes the content or design.

## Browse sample presentations

A comparison and a photographic essay need different layouts. These two decks show how SlidePoise adapts the composition to the content while maintaining a shared visual style across each presentation.

<table>
  <tr>
    <th width="50%">Consulting</th>
    <th width="50%">Editorial</th>
  </tr>
  <tr>
    <td><a href="https://slidepoise.github.io/?deck=consulting-ai-transformation&amp;slide=s05-investment-decision#examples"><img src="examples/consulting-ai-transformation/assets/s05-investment-decision-render.png" alt="Consulting slide showing investment assumptions, sensitivity tables and decision criteria" width="800"></a></td>
    <td><a href="https://slidepoise.github.io/?deck=personal-thinking-system&amp;slide=s04-trace#examples"><img src="examples/personal-thinking-system/assets/s04-trace-render.png" alt="Editorial slide combining typography, source records and original artwork" width="800"></a></td>
  </tr>
  <tr>
    <td>A recommendation for an AI pilot, supported by financial assumptions, a delivery plan and decision criteria.</td>
    <td>A personal thinking system expressed through typography, photography and separate illustrations.</td>
  </tr>
  <tr>
    <td><a href="examples/consulting-ai-transformation/deliverables/presentation.pptx">Download PowerPoint</a></td>
    <td><a href="examples/personal-thinking-system/deliverables/presentation.pptx">Download PowerPoint</a></td>
  </tr>
</table>

[Browse both decks](https://slidepoise.github.io/#examples), [inspect how individual objects are reconstructed](https://slidepoise.github.io/#build-slides), or [compare the design and PowerPoint render](https://slidepoise.github.io/#review-slide). The consulting sample uses a fictional firm and illustrative figures.

## Use your own style and assets

Save fonts, colours, design guidance and resource choices in a **Profile**, a reusable style configuration. The included [Consulting, Editorial Archive and Monochrome Modern profiles](profiles/README.md) provide starting points that you can adapt with your Agent.

The [public PwC and Strategy& reference collection](library-sets/visual_references/pwc-public-references/README.md) includes a complete consulting deck and indexed pages from related publications. For each slide, the Agent retrieves candidates by communication purpose and information structure, then inspects and selects useful precedents. Source provenance and exclusions stay attached to the selected pages. Private references remain in your local shared libraries.

Visual references, icons and reusable PowerPoint components live in shared **Library Sets**. Each profile can select whole sets or individual items, and you can change its selection in Console. New profiles reuse existing resources without copying them. Ask the Agent to import your own reusable files and it registers them for Console and skill retrieval. Remix Icon and Material Design Icons (MDI) supply open-source icons. Fine is the default icon weight. Wikimedia Commons supplies exact logos and public media, and you can add your own files. The Agent compares icon weight and silhouette at the intended slide size. Useful symbols introduced by image generation prompt another library search. Reconstruction restores selected canonical artwork and retains its source notices.

Small generated illustrations can be refined separately at higher resolution, including transparent backgrounds. The Agent checks them in the chosen composition before replacing the original image regions. The [third editorial slide](examples/personal-thinking-system/assets/s03-practice-render.png) uses three such illustrations.

## Adjust your saved preferences

Your Agent can manage styles, resource libraries and image-generation settings through conversation. The optional Local Console lets you browse and adjust the same preferences. After installation, ask your Agent to open it or run

```bash
npx github:henryhyw/slidepoise console
```

Saved settings apply to future presentations. Ask the Agent to adjust a presentation already in progress, or use its session panel for changes that apply only to that deck.

[Try the Console demo](https://slidepoise.github.io/#console) using the website’s sample settings.


## How it works

The Agent makes the content and design decisions. Local tools provide measurement, construction and rendering so the Agent can inspect what the PowerPoint actually contains.

### Plan the content

You and the Agent establish the audience, message and supporting material. The Agent develops the slide sequence and identifies what each slide needs to communicate.

### Generate slide images guided by content and references

The Agent searches the indexed reference library for useful visual precedents, inspects relevant icons, logos and native components, then selects resources for each slide. A [contact sheet](https://slidepoise.github.io/#design-slides) combines their previews with the chosen style in a form you can inspect. The image model receives this sheet alongside the slide instructions. The Agent checks the generated image against the brief for content, readability and layout before reconstruction. You can review a representative design before the Agent continues or ask it to complete the deck autonomously.

### Reconstruct the design as editable PowerPoint objects

The Agent identifies what the chosen image contains and which parts belong together. A chart’s bars, labels and values are recorded as one chart in a **semantic map**, an object-level description of the design. **OpenCV**, a computer-vision library, measures the assigned image regions. The reconstruction compiler combines those measurements with the semantic map and original assets. **PptxGenJS** builds the PowerPoint objects, including charts linked to their data.

Text, tables, shapes and connectors remain editable. Photographs, textures and illustrations are placed as separate images whose size, position and layering can be adjusted. Shared headers, footers and page numbers are added directly in PowerPoint.

Reconstruction can also correct defects in the generated image, including incorrect text, distorted icons and uneven alignment. The brief, source data and original assets guide these corrections while the chosen composition is preserved. [Inspect objects and compare all five consulting slides](https://slidepoise.github.io/#build-slides) to explore the generated designs and reconstructed PowerPoint renders.

<details>
<summary>See an actual PowerPoint edit</summary>

In this example, the title was edited and a chart value changed from 1,944 to 1,620. The bar and its label update in PowerPoint.

![PowerPoint renders before and after editing native text and chart data](examples/consulting-ai-transformation/run/work/native-edit-proof/comparison.png)

</details>

### Review the rendered presentation

The Agent compares the PowerPoint renders with the selected designs and the content plan. It checks relationships such as which objects an arrow connects, resolves text-fitting problems and reviews typography, colour and spacing across the deck. You can then revise a particular object, change one slide or reorder the presentation. Affected slides can be rebuilt individually.

## See how the Agent coordinates SlidePoise

The Agent directs the work and judges the results. The diagram shows how the content plan, references, generated images and local tools contribute to the editable deck. Its legend distinguishes inputs, actions and revision paths.

[![Four stages of SlidePoise. Content planning, visual design with retrieval and generation, native reconstruction, and visual review.](docs/images/slidepoise-architecture.png)](docs/images/slidepoise-architecture.svg)

The [technical architecture](docs/ARCHITECTURE.md) explains the semantic map, measurement evidence and reconstruction pipeline in detail.

## Get started

You need **Python 3.10+, Node.js 18+ with npm 9+, and an Agent that can run local commands and inspect images**.

Codex is the primary, end-to-end tested environment. Setup also supports Claude Code and Qoder. They use the same skill and local runtime through a connected image generator or manual image exchange. See the [image-generation guide](docs/IMAGE_GENERATION.md) for platform setup and tool selection.

### Ask your Agent

Paste this into your Agent to handle installation and setup.

```text
Install and set up SlidePoise for me from https://github.com/henryhyw/slidepoise.
```

### Install from your terminal

```bash
npx github:henryhyw/slidepoise setup
```

Setup registers the skill with detected Agent platforms and installs its local tools. Use `--agent codex`, `--agent claude` or `--agent qoder` to select a platform. Restart your Agent or reload its skills afterwards.

<details>
<summary>Local tools and preview requirements</summary>

Setup prepares an isolated Python environment for OpenCV, Pillow, NumPy and python-pptx, plus a Node.js runtime for PptxGenJS and JSZip. Reusable styles and asset libraries are stored under `~/.slidepoise`.

LibreOffice and Poppler produce slide previews for review. Setup installs missing preview tools through Homebrew on macOS, winget on Windows, or apt on Debian/Ubuntu. Homebrew must already be available on macOS. These system packages may request administrator access.

Your environment supplies image-generation access and fonts. Font substitutions or a different Office reader can change text wrapping and appearance. Run the installation check if setup reports a missing tool.

```bash
npx github:henryhyw/slidepoise doctor
```

The [usage guide](docs/USAGE.md) covers installation details, updates and resource management.

</details>

### Create a presentation

Give the Agent your source material, audience and intended outcome. For example

```text
Use SlidePoise to create a five-slide presentation for our leadership team
about an AI pilot, using the attached research and cost estimates.
Make the recommendation and its assumptions clear. Use the Consulting style
and show me one sample slide before completing the editable PowerPoint.
```

To generate images in another app, ask for manual image generation. The Agent prepares the prompt and reference files, then continues when you return the image.

## Develop and contribute

The self-contained skill and PowerPoint renderer live in [`slidepoise/`](slidepoise/). [`framework/`](framework/) contains installation and local services. Reusable styles and assets live in [`profiles/`](profiles/) and [`library-sets/`](library-sets/). [`webapp/`](webapp/) contains the optional Console and session controls.

<details>
<summary>Set up a development checkout and run tests</summary>

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev,runtime]'
npm ci
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
npm test
```

On Windows, use the executables in `.venv\Scripts`.

</details>

Read [CONTRIBUTING.md](CONTRIBUTING.md) for development guidance. Report bugs through [GitHub issues](https://github.com/henryhyw/slidepoise/issues) and security concerns through [SECURITY.md](SECURITY.md).

[MIT license](LICENSE) · [Designed by Henry W.](https://www.henryw.me/)
