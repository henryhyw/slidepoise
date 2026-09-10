# Sample presentations

The samples retain generated designs, editable PowerPoint files and reconstruction evidence. Each `showcase.json` uses paths relative to its example directory.

| Example | Content |
| --- | --- |
| [Consulting](../examples/consulting-ai-transformation/) | An illustrative AI pilot recommendation |
| [Editorial](../examples/personal-thinking-system/) | An essay about AI and personal thinking |

Open the [project page](https://www.henryw.me/slidepoise/docs/site/) to compare designs and rendered slides, inspect native objects and download either PowerPoint.

The `run/` directories record how the samples were produced. Their prompts and review records preserve original profile IDs and source paths as historical evidence. Use the CLI to start a new presentation with current profiles. Do not copy an old run's resolved configuration into a new project.

The native-object export utility in `docs/site/extract_objects.py` reads delivered PowerPoint geometry for the browser inspector. The project page itself is maintained in the [website repository](https://github.com/henryhyw/personalpage/tree/main/public/slidepoise). Website changes and product changes have separate test suites.
