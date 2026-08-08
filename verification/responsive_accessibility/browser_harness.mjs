/**
 * Node harness for Slice 14.11 browser overflow checks.
 *
 * Invoked by the Python verifier when docs/node_modules/playwright is available.
 * Input JSON on stdin:
 *   { baseAssessmentDir, docsDist, pages: [{surface, route, docs}], widths: number[] }
 * Output JSON on stdout.
 */
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { join, extname } from "node:path";

const require = createRequire(import.meta.url);
const docsPlaywright = join(
  process.cwd(),
  "docs/node_modules/playwright",
);
let chromium;
try {
  ({ chromium } = require(docsPlaywright));
} catch (error) {
  process.stdout.write(
    JSON.stringify({
      available: false,
      detail: `playwright_require:${error.name || "Error"}`,
      pages: [],
    }),
  );
  process.exit(0);
}

const input = JSON.parse(readFileSync(0, "utf8"));
const widths = input.widths || [320, 375, 390, 768, 1024, 1280, 1440];

function contentType(filePath) {
  switch (extname(filePath)) {
    case ".html":
      return "text/html; charset=utf-8";
    case ".css":
      return "text/css; charset=utf-8";
    case ".js":
      return "text/javascript; charset=utf-8";
    case ".svg":
      return "image/svg+xml";
    case ".png":
      return "image/png";
    case ".woff2":
      return "font/woff2";
    default:
      return "application/octet-stream";
  }
}

function serve(root) {
  return new Promise((resolve) => {
    const server = createServer((req, res) => {
      const url = new URL(req.url, "http://127.0.0.1");
      let relative = decodeURIComponent(url.pathname);
      if (relative.endsWith("/")) relative += "index.html";
      if (relative === "/") relative = "/index.html";
      const filePath = join(root, relative.replace(/^\//, ""));
      if (!existsSync(filePath)) {
        res.writeHead(404);
        res.end("missing");
        return;
      }
      res.writeHead(200, { "Content-Type": contentType(filePath) });
      res.end(readFileSync(filePath));
    });
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({ server, base: `http://127.0.0.1:${port}` });
    });
  });
}

const assessment = await serve(input.baseAssessmentDir);
const docs = input.docsDist ? await serve(input.docsDist) : null;

const browser = await chromium.launch({ headless: true });
const pages = [];
try {
  for (const pageSpec of input.pages) {
    const origin = pageSpec.docs ? docs?.base : assessment.base;
    if (!origin) continue;
    for (const width of widths) {
      const page = await browser.newPage({
        viewport: { width, height: 900 },
      });
      await page.goto(`${origin}/${pageSpec.route}`, {
        waitUntil: "domcontentloaded",
        timeout: 20000,
      });
      const metrics = await page.evaluate(() => {
        const el = document.documentElement;
        const before = el.scrollLeft;
        el.scrollLeft = el.scrollWidth;
        const scrolled = el.scrollLeft > 0;
        el.scrollLeft = before;
        return {
          pageOverflow: scrolled,
          scrollWidth: el.scrollWidth,
          clientWidth: el.clientWidth,
          hasSkip: Boolean(
            document.querySelector("a.skip-link, a.VPSkipLink"),
          ),
          hasMain: Boolean(
            document.querySelector(
              "main, [role='main'], #VPContent, #main-content, #main",
            ),
          ),
          h1Count: document.querySelectorAll("h1").length,
        };
      });
      await page.close();
      pages.push({
        surface: pageSpec.surface,
        route: pageSpec.route,
        width_px: width,
        page_overflow: metrics.pageOverflow,
        scroll_width: metrics.scrollWidth,
        client_width: metrics.clientWidth,
        has_skip: metrics.hasSkip,
        has_main: metrics.hasMain,
        h1_count: metrics.h1Count,
      });
    }
  }
} finally {
  await browser.close();
  assessment.server.close();
  docs?.server.close();
}

process.stdout.write(
  JSON.stringify({
    available: true,
    engine: "chromium",
    detail: "node_playwright_chromium",
    pages,
  }),
);
