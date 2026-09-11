# Runtime maintenance audit

Reviewed on 11 September 2026. This review covered installation and upgrades, image-generation handoffs, configuration changes, Console routes, packaged scripts and their callers, and reconstruction checks. It also examined the Windows CI failures from the 0.8.0 release.

## Corrected behaviour

| Finding | Correction | Verification |
| --- | --- | --- |
| Windows rewrote line endings in exported generation prompts. | Write the compiled UTF-8 prompt as bytes. | Compare the ZIP entry with the exact compiled prompt. |
| Windows paths in the reference manifest did not match ZIP entry names. | Use forward slashes for portable bundle paths on every platform. | Read each manifest reference from the ZIP, then import the returned image. |
| A failed skill copy could leave the previous installation archived and the replacement incomplete. | Prepare the replacement before touching the installed skill. Restore the previous directory if replacement fails. | Simulate copy and replacement failures and inspect the preserved installation. |
| Catalog preflight could substitute bundled data for an explicitly supplied missing library, or pass an empty profiles directory. | Report missing or empty inputs and honour the requested library location. | Exercise both missing-library and empty-profile cases. |
| Malformed generation modes could raise a Python type error. | Validate types before checking supported values. | Reject malformed settings without changing the saved config. |

The distribution test also attempted to install system preview applications while checking wheel contents and execution outside the checkout. That test now isolates package installation. Preview installation has separate tests for package-manager selection, partial failures and executable discovery. The CI preview job installs LibreOffice and Poppler and renders actual PowerPoint files.

## Removed paths

- `manage_library.py` had no callers and wrote icons and components into the retired profile-private layout. The maintained Profile and Library Set APIs provide the current authoring path.
- `collect_reconstruction_evidence.py` had no callers and repeated a partial collection of checks outside the active reconstruction pipeline. Contract construction, scene compilation and release evidence remain responsible for those checks.
- `extract_generation_region.py` had no callers and duplicated content-region cropping. The maintained visual comparison utility already crops full renders using the resolved frame.
- The Console server retained an unused run-creation wrapper, a cached registry path and a workspace-directory creation side effect. Conversation and the CLI use the shared session API.
- Five unused imports were removed.

The remaining evidence collectors produce geometry, asset bindings, rendered-text findings or package checks used by the reconstruction workflow. Migration code preserves existing user content and older run references. Standalone asset inspection and skill packaging remain useful utilities. These were retained.

## Limits

Passing tests does not establish visual quality for every future presentation. Agent review of actual renders remains required. Claude Code and Qoder end-to-end presentation runs are still unverified in those hosts. The cross-platform suite checks local runtime behaviour and installation contracts.
