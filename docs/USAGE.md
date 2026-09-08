# Usage

SlidePoise is a Codex skill and local runtime for creating editable presentations. The Agent develops the content and visual direction, interprets the generated design as meaningful objects, and reviews the actual PowerPoint render. Local tools supply measurement, text fitting, native construction and deck assembly.

The [README](../README.md) introduces the project and shows sample presentations. This guide covers installation, your first request and reusable visual settings. The current integration has been exercised with Codex. Other Agent hosts need their own integration checks.

## Quick start

Before setup, have Python 3.10+, Node.js 18+, npm 9+, and Codex with image generation available.

```bash
npx github:henryhyw/slidepoise setup
```

Setup may ask whether to install the Codex skill and Node dependencies. Keep those choices enabled for the usual installation. Codex must be detectable through its executable or an existing `~/.codex/skills` directory for automatic skill registration.

| Setup prepares | Default location |
| --- | --- |
| Isolated Python environment with Pillow, python-pptx, NumPy and OpenCV | `~/.slidepoise/python/` |
| PptxGenJS and JSZip for native construction | `~/.slidepoise/node/` |
| Reusable Profiles and Library Sets | `~/.slidepoise/profiles/` and `~/.slidepoise/library-sets/` |
| Codex skill and its self-contained reconstruction runtime | `~/.codex/skills/slidepoise/` |

Check the installation with

```bash
npx github:henryhyw/slidepoise doctor
```

Setup also prepares local previews. LibreOffice opens and renders the PowerPoint. Poppler converts the rendered pages to images for review. Missing tools are installed with Homebrew on macOS, winget on Windows, or apt on Debian/Ubuntu. These system packages may request administrator access. On macOS, Homebrew must already be installed. Other Linux distributions need equivalent packages from their own package manager.

Setup checks both executables after installation and reports an incomplete installation as an error. Resolve the reported issue and rerun the same command. If your Agent host already provides PowerPoint rendering, advanced users can pass `--skip-preview`. Codex, image generation and fonts remain part of your environment.

Then start a presentation in Codex.

```text
$slidepoise

Create a five-slide presentation for our leadership team about an AI pilot.
Use the Consulting Profile. Develop a clear recommendation, make the
assumptions explicit, and show me one sample before finishing the deck.
Deliver an editable PowerPoint.
```

Include the source material, intended audience and decision when you have them. You can request a specific style, ask for feedback at selected points or let the Agent proceed autonomously. Follow-up requests can revise one page, reorder the argument or change the visual direction.

OpenCV measures the geometry and colour of objects identified by the Agent.

## From the request to the deck

The Agent develops the argument and a shared visual direction before producing the pages. It identifies elements that serve the same purpose across the deck, including small recurring labels and page identifiers, and chooses their treatment together. Layouts can vary with the message. New repeated elements found in generated designs or actual renders become part of that same review.

Each image call uses one request compiled from the current content, canvas, references and shared design. The Agent sends that prompt and its recorded attachments to the image tool. Changes to the direction update those inputs before another request is compiled. You can guide these decisions in conversation without managing the intermediate files.

Generated images contain the slide's content area. Shared headers, footers and page numbers are added later in PowerPoint through its inherited frame. The enabled frame heights are subtracted from the full slide before generation. The content image is reconstructed in that reserved area without stretching.

The Agent interprets the selected image as meaningful objects, inspects OpenCV's measured evidence, and reviews the rendered PowerPoint. It compares the content crop with the generated target and the full pages with one another. Repeated typography, callouts, accents and frame details receive a separate visual calibration across the deck. A successful build or separate page reviews do not establish that consistency.

Routine corrections belong to the Agent. It checks the output against your brief as well as the generated design, inspects rendered-text discrepancies, and revisits the relevant inputs when something is missing or does not fit. When the host supports subagents, a separate reviewer inspects decks and complex slides before delivery. This reduces dependence on the author spotting its own mistakes. The [review evaluation](quality/autonomous-review.md) records what has been tested and the remaining limits.

## Install from a checkout

Use the same managed installation from the repository root.

```bash
npx . setup
```

Alternatively, install into a Python environment you manage.

```bash
python -m venv .venv
.venv/bin/pip install -e '.[runtime]'
npm ci
.venv/bin/slidepoise setup
```

On Windows, use `.venv\Scripts\pip.exe` and `.venv\Scripts\slidepoise.exe`. You can also use `pipx install '.[runtime]'` or `uv tool install '.[runtime]'` from the checkout, followed by `slidepoise setup`. These routes use their own Python environment.

Use `npx . setup --skip-python` only when the Python environment selected by the launcher already contains SlidePoise and its runtime dependencies. The launcher prefers an existing managed Python environment, then `PYTHON` when set, then the system Python command.

Setup copies reusable resources into the external framework home and prepares workspace and cache folders. It archives changed Codex skill content before replacement. Repeating setup with identical skill content does not create another backup. `SLIDEPOISE_HOME` selects a custom framework home.

## CLI

The GitHub installer keeps the working CLI inside SlidePoise's isolated Python environment. On macOS and Linux, use `~/.slidepoise/python/bin/slidepoise`. On Windows, use `%USERPROFILE%\.slidepoise\python\Scripts\slidepoise.exe`. A checkout or `pipx` installation also provides the shorter `slidepoise` command shown below.

```bash
slidepoise doctor
slidepoise profile list
slidepoise profile show personal-website
slidepoise profile select personal-website
slidepoise profile create "My Studio" --based-on personal-website
slidepoise profile add-resource my-studio visual_references reference.png --name "Editorial rhythm" --description "Asymmetric type and image treatment"
slidepoise library list
slidepoise library create icons "Research symbols"
slidepoise library add-resource research-symbols icon.svg --name "Research" --license "CC0"
slidepoise console
```

## Isolated profile structure

```text
profiles/<profile-id>/
  profile.json
  libraries/
    visual_references/catalog.json

library-sets/
  catalog.json
  icons/<set-id>/catalog.json
  components/<set-id>/catalog.json
```

Visual references belong to a profile because they define its point of view. Icons and components belong to coherent Library Sets because multiple profiles can share them without duplication. A profile selects complete sets. A run may temporarily override the captured selection.

Remix Icon and Wikimedia identity assets are remote Library Sets. The Agent inspects identity, visual fit, license terms, and provenance before selecting an asset. Retrieved files remain in the run cache.

Profiles are user-owned and can evolve through ordinary Agent conversation or the Console. The Agent can create a profile from the closest included starting point, translate the user's references and intent into guidance, and add an approved visual reference to the profile's private catalog. A run upload remains session-only until the user indicates that it should influence future work.

Profiles can specify a palette, typography, density, or icon treatment, express those values as guidance, or leave the decision to the Agent. Concrete fallback values remain available for reconstruction even when image generation has visual freedom.

## Installed layout

```text
~/.codex/skills/slidepoise/      stable Agent entrypoint and reconstruction runtime
~/.slidepoise/config.json        framework defaults and global provider switches
~/.slidepoise/profiles/          isolated guidance profiles and their libraries
~/.slidepoise/library-sets/      reusable icon and component families
~/.slidepoise/settings.json      active profile
~/.slidepoise/node/              PptxGenJS and Node runtime dependencies
~/.slidepoise/python/            npx-managed Python environment, when npx setup is used
~/.slidepoise/workspace/         slide runs and Console registry
~/.slidepoise/cache/             remote run assets and reusable runtime cache
~/.slidepoise/archive/           local recovery backups, created only when needed
```

The skill, config, and at least one profile are the working core. `settings.json` remembers the current profile. Python and Node dependencies are needed for measurement and PowerPoint construction, but their location depends on the installation route. A pip or uv installation uses its own Python environment and does not also need `~/.slidepoise/python/`. The workspace and cache hold generated local data.

`archive/` is not an installed component or a dependency. A clean installation does not create it. Updates create a backup only when replacing a changed skill, migrating a config, or retiring bundled profile files. Repeating setup with an identical skill does not create another copy. Backups never participate in generation and are excluded from the distribution. Remove a particular backup only when you no longer need it for recovery. The repository's historical `archive/` is separate and is never copied into a new installation.

### Upgrading from the former name

Default setup moves an existing `~/.slidecraft/` to `~/.slidepoise/` if the new directory does not exist. It leaves a compatibility symlink for historical absolute paths and virtualenv launchers. This is one data directory, not two installations. Historical prompts, run artifacts, reviews, and hashes are not rewritten. An existing `~/.codex/skills/slidecraft/` is archived when the new skill is installed, leaving only `~/.codex/skills/slidepoise/` discoverable. If both data directories already exist, setup stops instead of merging or overwriting them. Custom homes require an explicit `SLIDEPOISE_HOME` value.

## Visual authority

Mechanical tools report machine-checkable facts and measurements only. They do not issue a visual or release verdict. The host Agent combines those facts with direct semantic and visual inspection. Font size, density, whitespace, balance, similarity, and professional quality remain Agent judgements.

User checkpoints are adaptive. The Agent may show an outline, style sheet, representative sample, or selected slide candidates when feedback would prevent material rework. A user who asks for a fully automatic deck does not need to approve every page. The Agent can add, remove, reorder, split, merge, and revise slides by updating the live deck outline and rebuilding only affected pages.

Connector routes also require an Agent-authored visual route decision. The PowerPoint renderer emits each polyline as one continuous editable object to prevent gaps at bends.

## Session panel

```bash
slidepoise panel --run /absolute/path/to/presentation
slidepoise panel --id <panel_id> --view style
```

The Agent opens this panel only when current-presentation controls would help. It shows the inherited Profile, density, typography, palette, icon treatment, Library Sets, uploads, and which values are overridden. It does not show workflow stages, approvals, progress, generated images, PowerPoint downloads, or project history. Those interactions stay in the conversation.

Applying an edit writes a durable event for the Agent. An override affects only the bound presentation and never changes the shared Profile. The panel must be opened with a known run. It has no presentation picker or project-management surface.

The standalone Console is available at `/console/` on the same local service. It manages global Profiles, Profile-owned references, Library Sets, and system capabilities. It does not manage presentation runs.

```bash
slidepoise run create "Executive summary"
slidepoise run show /absolute/path/to/run
slidepoise run resolve /absolute/path/to/run
slidepoise run sync /absolute/path/to/run
slidepoise run events /absolute/path/to/run
slidepoise run ack-events /absolute/path/to/run --ids <event-id> --expected <revision>
```

Every run contains `work/deck-outline.json`, even for a one-slide request. Slide IDs stay stable while the ordered outline changes. Each slide keeps its own generation, semantic mapping, measurement, and reconstruction artifacts. `render-deck` assembles constructor scenes in the current outline order.

Earlier checkout versions exposed `run activity` and `run publish` for a stage-based display that the current product no longer uses. Those commands have been removed. Progress belongs in the Agent conversation. Use `run sync` to read durable panel changes and current settings, `run ack-events` after adopting those changes, and `run archive` to preserve the current presentation before revising it. Existing `work/activity.json` and `work/stage-selections.json` files remain untouched and are included in historical snapshots.

## Validation

```bash
python slidepoise/scripts/preflight_config.py framework/defaults/slidepoise-config.json
python slidepoise/scripts/preflight_catalogs.py --profiles-root profiles
python slidepoise/scripts/audit_skill_boundaries.py
python -m pytest
node --test tests/console_interactions.test.mjs tests/panel_interactions.test.mjs
```

## Preview package sources

The installer uses the maintained [Homebrew LibreOffice cask](https://formulae.brew.sh/cask/libreoffice) and [Poppler formula](https://formulae.brew.sh/formula/poppler), the corresponding [Microsoft winget community manifests](https://github.com/microsoft/winget-pkgs), and Debian/Ubuntu packages `libreoffice-impress` and `poppler-utils`. It reuses tools already installed on your computer.
