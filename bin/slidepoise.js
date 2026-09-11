#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const args = process.argv.slice(2);
const command = args[0];
const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const frameworkHome = path.resolve(process.env.SLIDEPOISE_HOME || path.join(os.homedir(), ".slidepoise"));
const managedPython = process.platform === "win32"
  ? path.join(frameworkHome, "python", "Scripts", "python.exe")
  : path.join(frameworkHome, "python", "bin", "python");

function checked(commandPath, commandArgs, { stdoutToStderr = false } = {}) {
  const result = spawnSync(commandPath, commandArgs, {
    cwd: packageRoot,
    stdio: stdoutToStderr ? ["inherit", "pipe", "inherit"] : "inherit",
    encoding: stdoutToStderr ? "utf8" : undefined,
  });
  if (stdoutToStderr && result.stdout) process.stderr.write(result.stdout);
  if ((result.status ?? 1) !== 0) process.exit(result.status ?? 1);
}

function bootstrapPython() {
  if (!fs.existsSync(managedPython)) {
    const basePython = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
    fs.mkdirSync(frameworkHome, { recursive: true });
    checked(basePython, ["-m", "venv", path.join(frameworkHome, "python")]);
  }
  const legacy = spawnSync(managedPython, ["-m", "pip", "show", "slidecraft-framework"], { stdio: "ignore" });
  if (legacy.status === 0) checked(managedPython, ["-m", "pip", "uninstall", "-y", "slidecraft-framework"], { stdoutToStderr: true });
  checked(managedPython, ["-m", "pip", "install", "--upgrade", `${packageRoot}[runtime]`], { stdoutToStderr: true });
}

function runPython(extraArgs) {
  const python = fs.existsSync(managedPython) ? managedPython : (process.env.PYTHON || (process.platform === "win32" ? "python" : "python3"));
  const result = spawnSync(python, ["-m", "framework.cli", ...extraArgs], {
    cwd: process.cwd(),
    env: { ...process.env, PYTHONPATH: [packageRoot, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter) },
    stdio: "inherit",
  });
  process.exit(result.status ?? 1);
}

async function interactiveSetup() {
  let setupArgs = ["setup"];
  const skipPython = args.includes("--skip-python");
  if (input.isTTY && output.isTTY) {
    output.write("\nSlidePoise framework setup\n\n");
    const prompts = createInterface({ input, output });
    const skill = (await prompts.question("Install or update the skill for your Agent platforms? [Y/n] ")).trim().toLowerCase();
    const node = (await prompts.question("Verify and install Node dependencies? [Y/n] ")).trim().toLowerCase();
    await prompts.close();
    if (skill === "n" || skill === "no") setupArgs.push("--skip-skill");
    if (node === "n" || node === "no") setupArgs.push("--skip-node");
  }
  // Resolve name migration before bootstrapping creates the new data directory.
  const migrationPython = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
  checked(migrationPython, ["-c", "from framework.migration import migrate_legacy_home; migrate_legacy_home()"]);
  if (!skipPython) bootstrapPython();
  setupArgs.push(...args.slice(1).filter(value => value !== "--skip-python"));
  runPython(setupArgs);
}

if (!command || ["-h", "--help"].includes(command)) {
  output.write(`
SlidePoise presentation framework

Usage
  npx . setup
  npx . setup --skip-python
  npx . doctor
  npx . profile list
  npx . profile select <profile-id>
  npx . console

From GitHub, use "npx github:henryhyw/slidepoise setup".
After the slidepoise package is published, use "npx slidepoise setup".

Setup creates an isolated Python runtime under ~/.slidepoise/python with OpenCV for visual measurement. Use --skip-python only when the active Python environment already contains SlidePoise runtime dependencies.

The stable Agent skill is installed separately from configurable profiles and their private libraries.
`);
  process.exit(0);
}

if (command === "setup") await interactiveSetup();
runPython(args);
