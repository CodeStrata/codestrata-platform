#!/usr/bin/env node
/**
 * Post-build validation for codestrata-docs.
 * - Internal link existence against dist HTML
 * - Forbidden content patterns (secrets, localhost, filesystem paths, platform internals)
 * - Required pages / assets
 * - Duplicate route heuristic via clean URL html files
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const dist = path.join(root, ".vitepress", "dist");

const errors = [];
const warnings = [];

function walk(dir, acc = []) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p, acc);
    else acc.push(p);
  }
  return acc;
}

if (!fs.existsSync(dist)) {
  console.error("FAIL: dist missing — run npm run build first");
  process.exit(1);
}

const requiredFiles = [
  "index.html",
  "favicon.svg",
  "robots.txt",
  "getting-started/index.html",
  "extensions/vscode.html",
  "extensions/cursor.html",
  "community/vs-platform.html",
  "platform/index.html",
];

for (const rel of requiredFiles) {
  if (!fs.existsSync(path.join(dist, rel))) {
    errors.push(`missing required dist file: ${rel}`);
  }
}

const htmlFiles = walk(dist).filter((f) => f.endsWith(".html"));
const routes = new Set();
for (const f of htmlFiles) {
  const rel = path.relative(dist, f).replace(/\\/g, "/");
  if (routes.has(rel)) errors.push(`duplicate route file: ${rel}`);
  routes.add(rel);
}

const forbidden = [
  { re: /BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY/i, msg: "private key material" },
  { re: /CODESTRATA_PLATFORM_API_KEY\s*=\s*['\"][^'\"]+['\"]/i, msg: "platform api key assignment" },
  {
    re: /https?:\/\/localhost(?::\d+)?/i,
    msg: "localhost URL in published content",
    skipRel:
      /^(EXTRACTION|VISUAL_REGRESSION|CI|DEPLOYMENT|ARCHITECTURE|MIGRATION_PLAN|WEBSITE_STYLE_ALIGNMENT|README|CONTRIBUTING)\.md$|^scripts\//,
  },
  {
    re: /https?:\/\/127\.0\.0\.1/i,
    msg: "loopback URL in published content",
    skipRel:
      /^(EXTRACTION|VISUAL_REGRESSION|CI|DEPLOYMENT|ARCHITECTURE|MIGRATION_PLAN|WEBSITE_STYLE_ALIGNMENT|README|CONTRIBUTING)\.md$|^scripts\//,
  },
  { re: /\/Users\/[^\s"'<>]+/g, msg: "absolute developer filesystem path" },
  { re: /file:\/\/\//i, msg: "file:// URL" },
];

const contentRoots = [root];
const scanExt = new Set([".md", ".html", ".ts", ".css", ".txt", ".svg", ".mjs", ".json"]);

function shouldScan(file) {
  const rel = path.relative(root, file).replace(/\\/g, "/");
  if (rel.startsWith("node_modules/")) return false;
  if (rel.startsWith(".vitepress/dist/")) return false;
  if (rel.startsWith(".vitepress/cache/")) return false;
  if (rel === "package-lock.json") return false;
  return scanExt.has(path.extname(file));
}

for (const base of contentRoots) {
  for (const file of walk(base).filter(shouldScan)) {
    const rel = path.relative(root, file).replace(/\\/g, "/");
    const text = fs.readFileSync(file, "utf8");
    for (const rule of forbidden) {
      if (rule.skipRel && rule.skipRel.test(rel)) continue;
      if (rule.re.test(text)) {
        errors.push(`${rule.msg}: ${rel}`);
      }
    }
  }
}

// Internal href check on dist HTML
const hrefRe = /href="(\/[^"#?]*|[^h][^"]*\.html)"/gi;
const assetExists = (urlPath) => {
  let p = urlPath.split("?")[0].split("#")[0];
  if (p.endsWith("/")) p += "index.html";
  else if (!path.extname(p)) p += ".html";
  const candidate = path.join(dist, p.replace(/^\//, ""));
  return fs.existsSync(candidate);
};

for (const file of htmlFiles) {
  const html = fs.readFileSync(file, "utf8");
  let m;
  const re = /href="(\/[^"]+)"/g;
  while ((m = re.exec(html))) {
    const href = m[1];
    if (href.startsWith("//")) continue;
    if (href.startsWith("/assets/")) {
      const asset = path.join(dist, href.slice(1));
      if (!fs.existsSync(asset)) errors.push(`missing asset ${href} from ${path.relative(dist, file)}`);
      continue;
    }
    // skip external-looking and hash-only handled by regex
    if (href.includes("mailto:")) continue;
    const clean = href.split("#")[0].split("?")[0];
    if (!clean || clean === "/") {
      if (!fs.existsSync(path.join(dist, "index.html"))) {
        errors.push(`broken href ${href} in ${path.relative(dist, file)}`);
      }
      continue;
    }
    // ignore vitepress theme chrome links that point to known anchors only
    if (clean.startsWith("/#")) continue;
    if (!assetExists(clean)) {
      // Allow sitemap etc.
      if (clean === "/sitemap.xml" || clean.endsWith(".xml")) {
        if (!fs.existsSync(path.join(dist, clean.slice(1)))) {
          warnings.push(`sitemap missing: ${clean}`);
        }
        continue;
      }
      errors.push(`broken internal href ${href} in ${path.relative(dist, file)}`);
    }
  }
}

// Metadata smoke: home title
const home = fs.readFileSync(path.join(dist, "index.html"), "utf8");
if (!/CodeStrata/i.test(home)) errors.push("home HTML missing CodeStrata brand");
if (!/Engineering Intelligence for Modern Software/i.test(home)) {
  errors.push("home HTML missing Engineering Intelligence for Modern Software title");
}
// Hero name must not restate brand or "Organizations"
if (/class="name"[^>]*>[\s\S]*?Organizations/i.test(home)) {
  errors.push("home hero title still includes Organizations");
}

// Footer / logo UX checks (Phase 13.5)
const footerMust = [
  "https://codestrata.ai/#how",
  "https://codestrata.ai/sample-report",
  "https://codestrata.ai/approach",
  "https://codestrata.ai/for-private-equity",
  "https://codestrata.ai/ecommerce-eol",
  "https://codestrata.ai/#engage",
  "https://codestrata.ai/#partner",
  "https://codestrata.ai/#faq",
  "https://codestrata.ai/privacy",
  "https://github.com/CodeStrata/codestrata-engine",
];
for (const href of footerMust) {
  if (!home.includes(href)) {
    errors.push(`home footer missing website link: ${href}`);
  }
}
if (home.includes("https://codestrata.ai/platform")) {
  errors.push("footer still links to broken codestrata.ai/platform (404)");
}
if (!home.includes('class="cs-docs-home"') && !home.includes("cs-docs-home")) {
  // Component may be hydrated client-side; check theme source instead.
  const themeIndex = fs.readFileSync(
    path.join(root, ".vitepress/theme/index.ts"),
    "utf8",
  );
  if (!themeIndex.includes("CsDocsHomeLink")) {
    errors.push("docs home nav link component not registered");
  }
}
if (!fs.existsSync(path.join(root, ".vitepress/theme/CsDocsHomeLink.vue"))) {
  errors.push("missing CsDocsHomeLink.vue");
}
const footerSrc = fs.readFileSync(
  path.join(root, ".vitepress/theme/CsFooter.vue"),
  "utf8",
);
if (!/rel="noopener noreferrer"/.test(footerSrc) && !/noopener noreferrer/.test(footerSrc)) {
  errors.push("CsFooter missing noopener noreferrer on external links");
}
const configSrc = fs.readFileSync(path.join(root, ".vitepress/config.ts"), "utf8");
if (!configSrc.includes('logoLink: "https://codestrata.ai/"')) {
  errors.push('config logoLink must be https://codestrata.ai/');
}
if (/codestrata ai --provider platform/.test(home)) {
  errors.push("published home must not advertise codestrata ai --provider platform");
}

console.log(`Scanned ${htmlFiles.length} HTML files in dist`);
for (const w of warnings) console.warn("WARN:", w);
if (errors.length) {
  for (const e of errors) console.error("ERROR:", e);
  console.error(`FAIL: ${errors.length} validation error(s)`);
  process.exit(1);
}
console.log("PASS: documentation validation");
