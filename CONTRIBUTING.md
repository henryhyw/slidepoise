# Contributing

SlidePoise turns a visually selected slide into an editable PowerPoint through a traceable reconstruction process. A useful contribution improves that user journey, protects a real failure boundary, or makes the project easier to understand and maintain.

Read [AGENTS.md](AGENTS.md), [the skill](slidepoise/SKILL.md), and [maintenance guidance](slidepoise/references/maintenance.md) before changing the framework. The packaged skill is the product source of truth. The host Agent owns visual, semantic, narrative, and interaction judgement. Runtime code measures, validates, transforms, constructs, and records evidence.

Use Python 3.10 or newer and Node 22 for development, matching the CI Node runtime. Install development dependencies from the repository root. Keep your normal SlidePoise home separate when exercising setup, migration, or profile changes.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,runtime]"
npm ci
```

On Windows, activate with `.venv\Scripts\Activate.ps1`. The tests create isolated homes and temporary presentations. They must never require personal assets, credentials, a model checkpoint, or a network model call.

Choose the layer that owns the behavior.

- `slidepoise/` contains portable host instructions, reconstruction contracts, and the packaged runtime.
- `framework/` owns installation, profiles, libraries, presentation workspaces, revisions, and persistence.
- `webapp/` provides optional profile management and current-presentation style controls.
- `profiles/` and `library-sets/` contain reusable design guidance and assets with provenance.

Keep a fix general. Do not encode a demonstration slide's identifiers, coordinates, text, or observed layout into the runtime. Preserve stable slide IDs, explicit deck ordering, and the ability to revise one page without rebuilding unrelated pages. OpenCV measures geometry and contours. Semantic ownership remains an Agent decision.

Write tests around a behavior someone depends on. A good test names its failure scenario, exercises the relevant boundary, and checks an observable result. For example, a stale style save must return a conflict without overwriting the newer change. Reordering two different scenes must change the actual page order in the PowerPoint package.

- Use focused unit tests for geometry, fitting, transforms, and malformed inputs where edge cases matter.
- Use integration tests for measurement-to-constructor handoffs, native PowerPoint structure, state revisions, uploads, and package installation outside the checkout.
- Use real renderer tests for output that can fail despite valid XML. The preview smoke checks English and Chinese text in an actual rendered PDF and preserves its PNG for inspection.
- Use interaction tests for concurrent saves, retries, editor preservation, and accessible dismissal behavior. They complement browser review and do not prove layout quality.

Avoid source-text assertions that freeze function names, copy, or implementation syntax. Avoid tests that merely check an output file exists, duplicate another scenario, or repeat the implementation as the expected answer. Replace weak coverage with a stronger observation before removing it. Test counts and visual similarity scores do not establish product quality.

Run the focused tests while developing, then the complete checks before a pull request.

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
npm test
python -m ruff check --select E9,F63,F7,F82 framework webapp slidepoise tests setup.py
python slidepoise/scripts/preflight_config.py framework/defaults/slidepoise-config.json
python slidepoise/scripts/preflight_catalogs.py --profiles-root profiles
python slidepoise/scripts/audit_skill_boundaries.py
```

In PowerShell, set `$env:PYTHONDONTWRITEBYTECODE = "1"` before running the Python commands. LibreOffice, `pdftoppm`, and `pdftotext` enable the real preview test. It skips locally when these dependencies are unavailable. CI installs them together with Noto CJK fonts and requires the test to run. Run it locally with `python -m pytest tests/test_preview_rendering.py -q --basetemp=workspace/preview-tests` to retain the artifacts.

The preview smoke verifies that both languages survive Office conversion and remain in the correct page order. It does not establish exact font matching across operating systems. A renderer may substitute an installed typeface while preserving readable text. Inspect the retained images and font evidence when typeface fidelity matters.

When a change can alter appearance, inspect representative targets, measurement overlays, and reconstructed renders at useful scale. Include Chinese or mixed-language text when changing typography, and multiple pages when changing assembly or object identifiers. Record what you saw and any remaining limitation. Mechanical checks support this review and cannot approve the design.

The pull request should explain the user's problem, resulting behavior, and validation. Include the smallest useful before-and-after evidence for visual changes. Describe migrations and preserved user data when changing storage. Demonstration numbers must be identified as illustrative. Keep generated showcase assets and their process evidence together so a future contributor can understand and reproduce the result.
