# Install SlidePoise for your user

Use this guide when the user gives you this repository and asks you to install or configure SlidePoise. Run the existing installer, inspect its results and configure image generation with the user. A repository checkout is optional.

## Check the environment

Identify the Agent platform you are running in. Supported registration targets are `codex`, `claude` for Claude Code, and `qoder` for Qoder. Desktop application detection alone does not establish which platform owns the current conversation.

Check that you can execute local commands, read and write files, and inspect images. A browser-only chat needs an environment with these capabilities before it can run the presentation workflow.

Check Python 3.10+, Node.js 18+ and npm 9+. If prerequisites are missing, install them through the user's available package manager within the permissions of your host. Preserve existing environments. If access or administrator privileges prevent installation, explain the specific remaining step. Do not describe an incomplete installation as ready.

## Run setup

Use the target for your current platform. For example, in Claude Code run

```bash
npx github:henryhyw/slidepoise setup --agent claude
```

Use `--agent codex` or `--agent qoder` for those platforms. Repeat `--agent` only when the user wants several installations. If you already have a checkout, `npx . setup --agent claude` from its root uses that source. Keep the checkout intact until installation finishes.

The command uses non-interactive defaults when run without a terminal. If npm asks to download the package, accept within the user's installation request. For an unattended invocation, npm's `--yes` option can acknowledge that package-download prompt. This is an execution detail and does not require another user setup step.

Setup creates an isolated runtime under `~/.slidepoise`, installs the bundled Profiles and Library Sets, and registers the skill. It also installs missing LibreOffice and Poppler preview tools through Homebrew, winget or apt. On macOS, Homebrew needs to be available first. On other Linux distributions, install equivalent preview packages through the available package manager.

Do not use `--force-profiles` during routine setup. Existing user Profiles and Library Sets should be preserved. Do not use dependency skip flags merely to make setup finish. `--skip-preview` is appropriate only if you have verified another available tool can render PowerPoint to images for review.

## Verify the installation

Inspect setup's exit status and JSON output. Check the selected platform appears in `skills`, Node dependencies were prepared and preview installation finished. A successful process exit alone does not establish that the requested platform was registered.

```bash
npx github:henryhyw/slidepoise doctor
npx github:henryhyw/slidepoise profile list
npx github:henryhyw/slidepoise generation show
```

Read the reported executable paths and capability fields. Confirm the installed `SKILL.md` exists in the platform's skill directory and its referenced scripts and runtime are present. `doctor` reports local facts. It does not verify image-generation access in the conversation.

Load the installed skill using your host's supported mechanism. If newly installed skills require a reload or new conversation, tell the user that specific step. Until then, you can read the installed `SKILL.md` directly. Use the GitHub command above if `slidepoise` is not on the shell's PATH. The managed CLI also lives at `~/.slidepoise/python/bin/slidepoise` on macOS and Linux, or `%USERPROFILE%\.slidepoise\python\Scripts\slidepoise.exe` on Windows.

## Configure image generation

Read the current preferences before changing them. Keep the user's existing selection unless they ask to change it. Follow the installed `references/image-generation.md` for capability discovery and the shared settings contract.

Discover tools actually exposed to this conversation, including native tools, MCP connections and installed integrations. Check their documented support for generation, image references, edits and transparent output as relevant. Never infer image-generation access from the Agent platform name or an installed executable.

For a new installation, automatic mode lets the Agent choose a compatible available tool for each request. If the user names a tool or model, save that preference after verifying the available integration. If no suitable tool is available, explain the available configuration options and offer manual generation. Do not silently select a paid service or invent a connection.

In manual mode, SlidePoise exports the exact compiled prompt and ordered visual references. The user generates an image in their chosen app and returns the downloaded file. The Agent imports it, reviews it and continues the same reconstruction workflow.

```bash
npx github:henryhyw/slidepoise generation configure --mode manual
```

The user can also change this in the local Console under **System → Image generation**. Store credentials in the provider's integration, never in SlidePoise preferences. Read the preferences back after saving. Global defaults apply to new presentations. Changes to an existing presentation use its session override.

## Finish with a useful handover

State which platform received the skill, whether local preview tools are ready, and the selected generation mode. Identify any unverified tool connection or required host reload. Do not claim a presentation workflow has been tested unless you actually ran one.

Invite the user to provide their presentation topic, audience and source material. They can develop the brief and visual style with you in conversation. The Console is optional.
