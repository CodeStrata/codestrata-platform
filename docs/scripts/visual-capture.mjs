#!/usr/bin/env node
/**
 * Capture documentation visual baselines.
 * Usage: DOCS_BASE_URL=http://127.0.0.1:4173 node scripts/visual-capture.mjs
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const outDir = path.join(root, "visual-baselines");
const base = process.env.DOCS_BASE_URL || "http://127.0.0.1:4173";

const shots = [
  { name: "home-dark-1280", path: "/", width: 1280, height: 800, theme: "dark" },
  { name: "home-light-1280", path: "/", width: 1280, height: 800, theme: "light" },
  { name: "home-mobile-390", path: "/", width: 390, height: 844, theme: "dark" },
  { name: "getting-started-1280", path: "/getting-started/", width: 1280, height: 800, theme: "dark" },
  { name: "reports-1280", path: "/reports/", width: 1280, height: 800, theme: "dark" },
  { name: "vscode-1280", path: "/extensions/vscode", width: 1280, height: 800, theme: "dark" },
  { name: "cursor-1280", path: "/extensions/cursor", width: 1280, height: 800, theme: "dark" },
  { name: "cli-1280", path: "/reference/cli", width: 1280, height: 800, theme: "dark" },
];

async function loadPlaywright() {
  const require = createRequire(import.meta.url);
  try {
    return require("playwright");
  } catch {
    try {
      return require("playwright-core");
    } catch {
      return null;
    }
  }
}

const pw = await loadPlaywright();
if (!pw) {
  console.error(
    "Playwright not installed. Run: npm i -D playwright && npx playwright install chromium",
  );
  process.exit(1);
}

fs.mkdirSync(outDir, { recursive: true });
const browser = await pw.chromium.launch({ headless: true });
const page = await browser.newPage();

for (const shot of shots) {
  await page.setViewportSize({ width: shot.width, height: shot.height });
  await page.goto(base + shot.path, { waitUntil: "networkidle" });
  await page.evaluate((theme) => {
    const root = document.documentElement;
    if (theme === "light") {
      root.classList.remove("dark");
      root.classList.add("light");
    } else {
      root.classList.add("dark");
      root.classList.remove("light");
    }
  }, shot.theme);
  await page.waitForTimeout(200);
  const file = path.join(outDir, `${shot.name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log("wrote", path.relative(root, file));
}

await browser.close();
console.log("PASS: visual baselines captured to visual-baselines/");
