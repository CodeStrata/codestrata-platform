#!/usr/bin/env node
/**
 * Theme validation: dark / light token application + persistence key presence.
 * Run against a preview server: DOCS_BASE_URL=http://127.0.0.1:4173 node scripts/theme-validate.mjs
 */
import { createRequire } from "node:module";

const base = process.env.DOCS_BASE_URL || "http://127.0.0.1:4173";
const require = createRequire(import.meta.url);

let pw;
try {
  pw = require("playwright");
} catch {
  console.error("playwright required: npm i -D playwright");
  process.exit(1);
}

const browser = await pw.chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];

await page.goto(base + "/", { waitUntil: "networkidle" });

async function readTokens() {
  return page.evaluate(() => {
    const cs = getComputedStyle(document.documentElement);
    return {
      darkClass: document.documentElement.classList.contains("dark"),
      dataTheme: document.documentElement.getAttribute("data-theme"),
      bg: cs.getPropertyValue("--bg").trim(),
      amber: cs.getPropertyValue("--amber").trim(),
      codeBg: cs.getPropertyValue("--code-bg").trim(),
      storage: localStorage.getItem("vitepress-theme-appearance"),
    };
  });
}

async function setTheme(mode) {
  await page.evaluate((mode) => {
    localStorage.setItem("vitepress-theme-appearance", mode);
  }, mode);
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(400);
}

// Dark
await setTheme("dark");
let t = await readTokens();
if (!t.darkClass) errors.push("dark mode missing .dark class");
if (t.bg !== "#0b0d10") errors.push(`dark --bg expected #0b0d10 got ${t.bg}`);
if (t.amber !== "#d98a3d") errors.push(`dark --amber expected #d98a3d got ${t.amber}`);
if (t.codeBg !== "#0d1014") errors.push(`dark --code-bg expected #0d1014 got ${t.codeBg}`);

// Toggle must exist (desktop nav)
const toggle = page.locator(".VPNavBar .VPSwitchAppearance").first();
const toggleCount = await page.locator(".VPSwitchAppearance").count();
if (toggleCount === 0) errors.push("theme toggle not found");
else {
  // Prefer visible nav-bar switch; force if in overflow
  const navToggle = page.locator('.VPNavBarAppearance .VPSwitchAppearance, .VPNavBar .VPSwitchAppearance').first();
  await navToggle.click({ force: true, timeout: 5000 }).catch(async () => {
    await page.locator(".VPSwitchAppearance").last().click({ force: true });
  });
  await page.waitForTimeout(400);
  t = await readTokens();
  if (t.darkClass) errors.push("toggle did not switch to light");
  if (t.bg !== "#ffffff") errors.push(`light --bg expected #ffffff got ${t.bg}`);
  if (t.codeBg !== "#0f1216") {
    errors.push(`light --code-bg should stay dark (#0f1216), got ${t.codeBg}`);
  }
  if (t.dataTheme && t.dataTheme !== "light") {
    errors.push(`data-theme expected light got ${t.dataTheme}`);
  }

  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(400);
  t = await readTokens();
  if (t.darkClass) errors.push("light preference did not persist across reload");
}

// auto / system preference storage
await setTheme("auto");
t = await readTokens();
if (t.storage !== "auto") errors.push(`expected storage auto, got ${t.storage}`);

await browser.close();

if (errors.length) {
  for (const e of errors) console.error("ERROR:", e);
  process.exit(1);
}
console.log("PASS: theme dark/light/toggle/persistence/auto validated");
