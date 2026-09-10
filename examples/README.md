# Sample presentations

Explore both decks on the [project page](https://www.henryw.me/slidepoise/docs/site/).

- [Consulting](consulting-ai-transformation/) presents an AI pilot recommendation with editable charts, tables and an operating model.
- [Editorial](personal-thinking-system/) combines native typography with photographic collage and transparent illustrations.

Each example includes a PowerPoint, previews, the selected designs and the inputs needed to reconstruct them. `showcase.json` identifies the current public assets. Earlier experiments are available in Git history.

## Rebuild a sample

After installing the development dependencies, run the packaged reconstruction path with the retained designs and semantic maps.

```bash
python examples/rebuild.py examples/consulting-ai-transformation --output-dir output/consulting-rebuild
```

Use a new output directory for each run. Add `--no-preview` to construct the PowerPoint without rendering images. Fonts and the preview renderer can affect the result. To compare a rebuild with the recorded images in the same environment, use `examples/verify_rebuild.py --help`.

These are reproducible construction inputs. Creating a new presentation starts with a new brief and Agent-led design.
