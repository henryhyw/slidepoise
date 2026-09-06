# Verification

The September 6, 2026 release candidate was checked on macOS with Python 3.12 and Node.js 22.

## Executed checks

- 270 Python tests cover generation inputs, measurement, native construction, installation, file revisions, Console saves and session isolation.
- 27 Node tests cover dialog behavior, full slide plans, reconstruction records, cancellation and the isolated Console demo.
- 20 static-site tests cover portable assets, source bindings and complete planning records.
- Skill boundaries, configuration and resource catalogs passed their packaged validators.
- The skill archive, wheel, source distribution and npm package contained the same 75 skill files.
- An isolated wheel installation completed setup and opened the packaged runtime outside the source checkout.
- The extracted runtime reconstructed and rendered both five-slide samples. Native slide, chart and frame XML matched the retained presentations. The text audit reported no findings.

## Browser review

The project page was inspected on desktop and at a 390-pixel mobile viewport. Editorial is selected by default. Visitors can switch between PowerPoint, comparison, generated design, element groups and OpenCV measurements. The interpretation viewer uses every retained semantic entity, and selected groups highlight their actual members. Pixel details come from the retained OpenCV records.

The embedded Console uses the actual Console interface with sample data. Font changes take effect in the demo, other browser tabs remain independent, and reloading resets the data. The iframe blocks network API calls and cannot reach an installed Console. The interaction gate and Done control were checked on desktop and mobile.

## Scope

These checks establish the behavior of this source and the retained samples. They do not guarantee identical results for every prompt, model, font or Office reader. The Agent must still inspect generated images and rendered PowerPoint pages, including consistency across the full deck.

CI repeats source tests on Windows, macOS and Linux with Python 3.10 and 3.12. A separate Linux job installs LibreOffice and Poppler and tests actual rendering. Check the repository’s Actions page for the results of the published commit.
