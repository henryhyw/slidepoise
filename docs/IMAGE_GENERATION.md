# Image generation and Agent platforms

SlidePoise is built and tested with Codex and its native image-generation tools. Claude Code and Qoder can use the same skill and local runtime with a connected image generator, including MCP, or a manual exchange. Every host needs local command execution, file access and image inspection.

## Install for your Agent

```bash
npx github:henryhyw/slidepoise setup
```

Setup detects supported installations. To choose a platform explicitly, add `--agent claude`, `--agent qoder` or `--agent codex`. Repeat the option to install for several platforms. All platforms receive the same skill and runtime.

| Platform | Skill directory | Generation access |
| --- | --- | --- |
| Codex | `~/.codex/skills/slidepoise/` | Available native tool, connected integration or manual exchange |
| Claude Code | `~/.claude/skills/slidepoise/` | Connected image tool, including MCP, or manual exchange |
| Qoder CLI | `~/.qoder/skills/slidepoise/` | Connected image tool, including MCP, or manual exchange |

Restart or reload skills after installation. Claude's [skill documentation](https://code.claude.com/docs/en/skills) and Qoder's [skill documentation](https://docs.qoder.com/cli/Skills) explain discovery. Their MCP documentation describes connecting tools for [Claude Code](https://code.claude.com/docs/en/mcp) and [Qoder](https://docs.qoder.com/cli/mcp-servers). QoderWork uses a separate application and skill directory.

The bundled presentations were produced in Codex. Automated tests cover the three installation paths, shared configuration, tool compatibility checks and manual exchanges. They do not replace end-to-end presentation runs inside Claude Code and Qoder, which remain to be verified.

## Let the Agent find a tool

Automatic mode is the default. The Agent inspects capabilities exposed in its current conversation, including connected MCP tools and installed image-generation skills. It checks whether a tool accepts the prompt and reference images and supports the requested operation. Finding an application on your computer is not proof of image-generation access.

If no suitable capability is connected, the Agent offers to help configure one or prepare a manual exchange. Install only integrations you intend to use. Authentication and API keys belong in the integration's own configuration.

## Choose a tool or model

Tell the Agent which image generator you want. It resolves the available tool and saves your preference. For example, ask it to use your connected image MCP tool for future decks, or use manual generation for the current presentation only.

The local Console has the same controls under **System → Image generation**. Choose Automatic, Choose a tool or Generate elsewhere. A model preference is optional. Some tools choose their own model and cannot honour a specific model selection. The Agent should make that limitation clear before using them.

For terminal use

```bash
slidepoise generation show
slidepoise generation configure --mode manual
slidepoise generation configure --mode auto
```

A selected tool can be saved with `--mode tool --tool <tool-id>`. Add `--model <model-id>` when supported. Use an empty string to clear a model preference. Add `--run <presentation-folder>` to change one presentation. Saved defaults are captured when a presentation starts, so changing a global preference does not silently alter work already in progress.

## Generate images yourself

Ask the Agent to use manual generation. It prepares a ZIP containing the exact prompt, numbered reference files and instructions. Attach the references in number order, paste the prompt into your image generator and return the original downloaded image.

The Agent checks that the request still matches the current plan and references. It inspects the image before building the PowerPoint. If you changed the plan while the image was being generated, it prepares an updated exchange. Slide corrections and individual transparent illustration edits work the same way.

For integrations, the exchange commands are

```bash
slidepoise generation export --request generation-request.json --output image-exchange
slidepoise generation import --handoff image-exchange --image downloaded.webp --output candidate.png
```

An imported file is a candidate for review. Its existence does not mean the design is accepted. The normal semantic interpretation, OpenCV measurement, reconstruction and visual review still follow.
