# SlidePoise

**Free-form AI slide design, reconstructed as editable PowerPoint.**

SlidePoise is an open-source Codex skill that uses image generation to explore free-form slide designs, then reconstructs the selected design as an editable PowerPoint. You and the Agent define the audience, argument, content and visual direction. The Agent interprets the chosen design, OpenCV measures its geometry, and local tools build the native PowerPoint objects.

The Agent decides what each element means, how the elements relate and whether the finished slide works. Computer vision handles pixel measurements. After reconstruction, the Agent compares the actual renders with the generated designs and checks recurring typography, colour, spacing, headers and footers across the full deck.

![SlidePoise architecture showing intent, image generation, Agent interpretation, OpenCV measurement, editable PowerPoint and deck review](docs/site/architecture.png)

[Get started](#get-started) · [Usage guide](docs/USAGE.md) · [Architecture](docs/ARCHITECTURE.md) · [Contribute](CONTRIBUTING.md)

## Sample presentations

The [project page](https://www.henryw.me/slidepoise/docs/site/) lets you inspect two complete decks slide by slide. Read each slide's plan, compare the generated design with the PowerPoint render, and inspect its element groups and OpenCV measurements.

| Consulting sample | Editorial sample |
| --- | --- |
| ![Consulting sample PowerPoint](examples/consulting-ai-transformation/assets/s02-opportunities-render.png) | ![Editorial sample PowerPoint](examples/personal-thinking-system/assets/s01-opening-render.png) |
| **Consulting** · An executive recommendation for an AI pilot, with editable charts and tables. | **Editorial** · A personal essay about thinking with AI, combining editable typography with photographic collage. |
| [Download PowerPoint](examples/consulting-ai-transformation/deliverables/presentation.pptx) | [Download PowerPoint](examples/personal-thinking-system/deliverables/presentation.pptx) |

The Consulting sample uses a fictional firm and illustrative figures. Profiles can describe other visual systems beyond the two shown here.

To open the project page locally, serve the checkout with `python -m http.server 8000` and visit `http://localhost:8000/docs/site/`.

## Get started

You need **Python 3.10+, Node.js 18+, npm 9+, and Codex with image generation**. Run

```bash
npx github:henryhyw/slidepoise setup
```

Setup creates an isolated local runtime, registers the skill, copies the included Profiles and Library Sets, and installs missing preview tools through Homebrew on macOS, winget on Windows, or apt on Debian/Ubuntu. Your system may request administrator access for those preview tools. SlidePoise uses fonts available on your machine.

<details>
<summary>Installation contents and optional dependencies</summary>

`npx` installs the Python measurement tools and Node.js PowerPoint renderer under `~/.slidepoise`. It registers the skill in `~/.codex/skills/slidepoise` when Codex is detected, and copies the bundled Profiles and Library Sets.

Python dependencies include Pillow, python-pptx, NumPy and OpenCV. The Node runtime uses PptxGenJS and JSZip. LibreOffice renders PowerPoint pages. Poppler converts those pages into images for review. Setup prepares these through the system package manager and checks that both executables are available. If installation cannot finish, it reports the missing tool and exits with an error so you can resolve the issue and rerun setup. Codex, image generation and fonts are supplied by your environment.

OpenCV measures object boundaries, colour and geometry for reconstruction.

</details>

Start a Codex conversation with `$slidepoise`. Describe the audience, the decision or story, the source material and any visual references you want the Agent to use.

```text
$slidepoise

Create a five-slide presentation for our leadership team about an AI pilot.
Use the Consulting Profile. Develop a clear recommendation, make the
assumptions explicit, and show me one sample before finishing the deck.
Deliver an editable PowerPoint.
```

The [usage guide](docs/USAGE.md) covers installation checks, Profile management and presentation controls.

## How it works

| Stage | Work |
| --- | --- |
| Plan | Decide what each slide needs to communicate and gather its supporting content. |
| Design | Generate compositions using your references and a shared visual direction. |
| Reconstruct | Identify objects, measure their geometry and build the PowerPoint. |
| Review | Compare actual renders with the designs and check consistency across pages. |

**Image generation receives the content area.** SlidePoise reserves space for enabled headers and footers before calculating the image aspect ratio. PowerPoint adds those shared elements after reconstruction, including native page-number fields.

**The Agent interprets the design. OpenCV measures it.** The Agent may identify a set of bars, labels and values as one chart. OpenCV measures the visible geometry within that assigned region. The renderer can then build a native chart linked to a workbook.

**The final review covers the whole presentation.** The Agent compares all rendered pages, identifies recurring roles such as titles, labels and folios, and corrects inconsistent treatment before delivery. The [architecture](docs/ARCHITECTURE.md) explains the division of responsibility.

Below, an edited copy has a new title and a chart value changed from 1,944 to 1,620. The bar and its label update in PowerPoint.

![Actual PowerPoint renders before and after editing native text and chart data](examples/consulting-ai-transformation/run/work/native-edit-proof/comparison.png)

## Visual references and Profiles

Profiles save typography, palette, density and visual references for future presentations. The repository includes Consulting, Editorial Archive and Monochrome Modern as starting points. Add your own references and let each slide's layout respond to its message.

Library Sets supply reusable icons and components. Use the local Console to manage your saved styles and resources. Ask Codex to open it, or run the following command after installation.

```bash
npx github:henryhyw/slidepoise console
```

[Try the interactive Console demo](https://www.henryw.me/slidepoise/docs/site/#console). It uses sample data and does not inspect your computer.

Saved changes apply to future presentations. A session panel adjusts a presentation already in progress without changing its saved Profile.

## Editability and compatibility

SlidePoise can construct native text, tables, charts, shapes, connectors and freeforms. Photographs, textures and expressive illustrations remain regional images. Separate text and table values do not gain spreadsheet formulas automatically.

The integration and samples have been tested with Codex. Local previews use LibreOffice and Poppler. Other Agent hosts need their own integration checks. Fonts are not bundled, and different fonts or Office readers can change text wrapping and appearance.

## Develop and contribute

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev,runtime]'
npm ci
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
npm test
```

On Windows, use the executables in `.venv\Scripts`.

The self-contained skill and renderer live in [`slidepoise/`](slidepoise/). [`framework/`](framework/) contains installation and local services. [`profiles/`](profiles/) and [`library-sets/`](library-sets/) hold reusable resources. [`webapp/`](webapp/) contains the optional controls.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before making changes. Report defects through [GitHub issues](https://github.com/henryhyw/slidepoise/issues) and security concerns through [SECURITY.md](SECURITY.md).

[MIT license](LICENSE)
