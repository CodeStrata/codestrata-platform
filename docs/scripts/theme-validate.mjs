#!/usr/bin/env node
/**
 * Theme validation against Design System tokens (Slice 14.2).
 * Run: DOCS_BASE_URL=http://127.0.0.1:4173 node scripts/theme-validate.mjs
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
      bg: cs.getPropertyValue("--bg").trim() || cs.getPropertyValue("--cs-bg").trim(),
      canvas: cs.getPropertyValue("--cs-canvas").trim(),
      tealDark: cs.getPropertyValue("--cs-teal-dark").trim(),
      codeBg: cs.getPropertyValue("--code-bg").trim() || cs.getPropertyValue("--vp-code-bg").trim(),
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

await setTheme("dark");
let t = await readTokens();
if (!t.darkClass) errors.push("dark mode missing .dark class");
if (t.canvas !== "#101a17" && t.bg !== "#101a17") {
  errors.push(`dark canvas/bg expected #101a17 got canvas=${t.canvas} bg=${t.bg}`);
}
if (t.tealDark !== "#0f5d54") {
  errors.push(`--cs-teal-dark expected #0f5d54 got ${t.tealDark}`);
}

const toggleCount = await page.locator(".VPSwitchAppearance").count();
if (toggleCount === 0) errors.push("theme toggle not found");
else {
  const navToggle = page
    .locator(".VPNavBarAppearance .VPSwitchAppearance, .VPNavBar .VPSwitchAppearance")
    .first();
  await navToggle.click({ force: true, timeout: 5000 }).catch(async () => {
    await page.locator(".VPSwitchAppearance").last().click({ force: true });
  });
  await page.waitForTimeout(400);
  t = await readTokens();
  if (t.darkClass) errors.push("toggle did not switch to light");
  if (t.canvas !== "#f4f6f3" && t.bg !== "#f4f6f3") {
    errors.push(`light canvas/bg expected #f4f6f3 got canvas=${t.canvas} bg=${t.bg}`);
  }
  if (t.dataTheme && t.dataTheme !== "light") {
    errors.push(`data-theme expected light got ${t.dataTheme}`);
  }

  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(400);
  t = await readTokens();
  if (t.darkClass) errors.push("light preference did not persist across reload");
}

await setTheme("auto");
t = await readTokens();
if (t.storage !== "auto") errors.push(`expected storage auto, got ${t.storage}`);

await browser.close();

if (errors.length) {
  for (const e of errors) console.error("ERROR:", e);
  process.exit(1);
}
console.log("PASS: theme dark/light/toggle/persistence/auto validated (Design System)");
