# Test-suite audit

Reviewed on 11 September 2026, starting from commit `1578899`. The reported 341 Python cases and 22 JavaScript cases included parameterized scenarios. Those counts described successful execution, not an assessment of each test's value.

This review examined test assertions, fixtures and the boundaries they exercise. Nine deliberate implementation faults were tried individually, with the original code restored after each experiment. This is a targeted audit, not an exhaustive mutation score.

## Gaps found and corrected

The JavaScript VM fixtures bypassed browser event wiring. Disconnecting the Console's image-generation button left all 22 tests green. Four browser scenarios now operate the actual Console and session panel against the real HTTP service at desktop and phone widths. They exercise default-profile selection, generation preferences, stale saves, presentation-only typography, uploads and backdrop dismissal. The disconnected button now fails in both viewport sizes.

The style-only reference-sheet test accepted a blank white PNG. It now checks that the authored palette swatches appear in the image. This establishes that the image carries those inputs. It does not assess the sheet's aesthetic quality.

The browser tests also found an existing save-refresh bug. A session style save requested a refresh while its editor was still open. The draft-protection guard suppressed that refresh, leaving stale values and inheritance labels until the next poll. The form now refreshes after a successful save closes the editor. Failed saves keep the editor and draft intact. Three premature refresh calls and their unused wrapper were removed.

## Deliberate faults

| Fault introduced | Observed result |
| --- | --- |
| Disconnect the generation settings button | Old JavaScript suite passed. New browser tests fail because the editor never opens. |
| Save a blank style reference sheet | Old test passed. Revised test fails on missing palette swatches. |
| Permit stale writes | HTTP tests fail when a conflicting save returns success. |
| Truncate the exported image prompt | Bundle test fails on the actual ZIP entry's bytes. |
| Remove transparency from the returned image | Import test fails on the saved pixel's missing alpha channel. |
| Remove failed-install rollback | Installation test fails because the previous skill file is missing. |
| Refresh Console while an editor is open | Interaction test detects the unwanted reload. |
| Emit horizontal bars for a column chart | PowerPoint package test detects the wrong chart direction. |
| Suppress missing-connection findings | Content-obligation test detects the missing findings after an arrow is removed. |

All nine faults are detected by the retained or revised checks. The experiments were local and are not shipped as another production script.

## Tests removed or narrowed

- Removed a repeated config-success test whose additional assertions only banned two result keys.
- Removed a pending-change test that checked prose and prohibited words without exercising adoption behaviour.
- Replaced an exact script-tag assertion with actual dismissal on both browser pages.
- Replaced a synthetic capability-dialog class check with a real click, populated details and viewport bounds.
- Replaced global counts of inheritance-label wording with checks on the affected and unaffected controls after a real save.
- Removed duplicated field assertions, exact control ordering and boilerplate prompt-copy assertions. Whole-intent propagation, payload scope and escaping checks remain.

Parameterized cases for malformed inputs, relationship direction, gesture cancellation and platform differences were retained. They exercise distinct failure conditions. Migration tests were retained because they protect installed user data. Native XML, rendered-text, portable-bundle and isolated-installation tests check actual artifacts across runtime boundaries.

## Verification

Local checks passed with 340 Python cases, 18 focused JavaScript cases and four browser scenarios. Configuration, catalogs, skill boundaries, Python lint checks and the four showcase object-extraction tests also passed. The npm package inspection confirmed that tests, browser binaries and temporary audit experiments are excluded. CI now includes a dedicated browser job alongside the existing platform, rendering and packaging jobs.

## Remaining limits

Browser automation currently runs in Chromium. This audit does not establish Safari or Firefox compatibility. Remote-library and image-tool contract tests use controlled responses and do not prove external service availability. Claude Code and Qoder end-to-end runs remain unverified in those hosts.

The suite still cannot establish visual quality for an arbitrary generated presentation. It checks explicit content obligations, geometry, files and rendered evidence. The Agent must inspect actual slides and discover omissions that were never included in those obligations.

Dependency scanning also reported high-severity denial-of-service advisories in `image-size`, a transitive dependency of PptxGenJS. This predates the new browser dependency and remains unresolved. The upstream advisories list no patched release. The scanner's proposed PptxGenJS downgrade is not a compatible fix. See [ICNS parser advisory](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr) and [JXL/HEIF parser advisory](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq).
