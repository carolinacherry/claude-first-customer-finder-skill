#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");

function usage() {
  console.log(`
First Customer Finder skill installer (Claude Code)

Usage:
  npx --yes claude-first-customer-finder-skill
  claude-first-customer-finder-skill --skills-dir ~/.claude/skills

Options:
  --skills-dir PATH  Install into a custom skills directory
  --help             Show this help
`);
}

function expandHome(value) {
  if (!value) return value;
  if (value === "~") return os.homedir();
  if (value.startsWith("~/")) return path.join(os.homedir(), value.slice(2));
  return value;
}

function parseArgs(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--help" || arg === "-h") {
      options.help = true;
      continue;
    }
    if (arg === "--skills-dir") {
      const value = argv[index + 1];
      if (!value) throw new Error("--skills-dir requires a value");
      options.skillsDir = expandHome(value);
      index += 1;
      continue;
    }
    throw new Error(`Unknown option: ${arg}`);
  }
  return options;
}

function defaultSkillsDir() {
  const configDir =
    process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude");
  return path.join(configDir, "skills");
}

function copyDirectory(source, destination) {
  fs.mkdirSync(destination, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const sourcePath = path.join(source, entry.name);
    const destinationPath = path.join(destination, entry.name);
    if (entry.isDirectory()) copyDirectory(sourcePath, destinationPath);
    else if (entry.isFile()) fs.copyFileSync(sourcePath, destinationPath);
  }
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    usage();
    return;
  }

  const source = path.resolve(__dirname, "..", "skills", "first-customer-finder");
  const skillsDir = path.resolve(options.skillsDir || defaultSkillsDir());
  const destination = path.join(skillsDir, "first-customer-finder");
  if (!fs.existsSync(source)) throw new Error(`Cannot find bundled skill at ${source}`);

  fs.mkdirSync(skillsDir, { recursive: true });
  fs.rmSync(destination, { recursive: true, force: true });
  copyDirectory(source, destination);

  console.log("Installed the first-customer-finder skill for Claude Code.");
  console.log(`Location: ${destination}`);
  console.log("");
  console.log("Start a new Claude Code session, then try:");
  console.log('  "Find ten potential first customers for https://example.com"');
}

try {
  main();
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}
