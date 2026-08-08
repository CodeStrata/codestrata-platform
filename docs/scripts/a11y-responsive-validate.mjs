/**
 * Slice 14.11 — representative docs overflow / landmark check via Playwright.
 *
 * Optional. The Python verifier also drives browser validation; this script is
 * a docs-local convenience that fails closed when Playwright is unavailable.
 */
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch {
  console.error("playwright unavailable — run static verifier instead");
  process.exit(2);
}

const base = process.env.DOCS_BASE_URL || "http://127.0.0.1:4173";
const widths = [320, 375, 768, 1280];
const routes = [
  "/",
  "/getting-started/",
  "/reference/cli.html",
  "/reference/public-contracts.html",
];

const browser = await chromium.launch({ headless: true });
let failed = 0;
try {
  for (const route of routes) {
    for (const width of widths) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      await page.goto(new URL(route, base).href, {
        waitUntil: "domcontentloaded",
        timeout: 15000,
      });
      const metrics = await page.evaluate(() => {
        const el = document.documentElement;
        const before = el.scrollLeft;
        el.scrollLeft = el.scrollWidth;
        const scrolled = el.scrollLeft > 0;
        el.scrollLeft = before;
        return {
          overflow: scrolled,
          skip: Boolean(document.querySelector("a.VPSkipLink, a.skip-link")),
          main: Boolean(document.querySelector("main, #VPContent")),
          h1: document.querySelectorAll("h1").length,
        };
      });
      await page.close();
      const ok = !metrics.overflow && metrics.skip && metrics.main && metrics.h1 === 1;
      console.log(
        JSON.stringify({ route, width, ...metrics, ok }),
      );
      if (!ok) failed += 1;
    }
  }
} finally {
  await browser.close();
}
process.exit(failed ? 1 : 0);

// Keep the file URL helper referenced so bundlers do not tree-shake unused imports.
void pathToFileURL;
