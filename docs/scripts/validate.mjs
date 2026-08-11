#!/usr/bin/env node
/**
 * Post-build validation for codestrata-docs (Community Edition, Slice 14.2).
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
  "favicon.ico",
  "favicon.png",
  "apple-touch-icon.png",
  "robots.txt",
  "getting-started/index.html",
  "getting-started/install.html",
  "getting-started/repository-initialization.html",
  "extensions/vscode.html",
  "assessments/index.html",
  "reports/index.html",
  "reports/engineering-intelligence.html",
  "reference/cli.html",
  "reference/configuration.html",
  "reference/api.html",
  "reference/community-api/index.html",
  "reference/telemetry.html",
  "security/privacy.html",
  "troubleshooting/index.html",
  "faq/index.html",
  "reference/release-notes.html",
];

for (const rel of requiredFiles) {
  if (!fs.existsSync(path.join(dist, rel))) {
    errors.push(`missing required dist file: ${rel}`);
  }
}

// Docs search REMOVED FOR v0.2.0 (Cloudflare cannot serve VitePress
// `@localSearchIndex*` chunks). VitePress still emits an empty
// `.VPNavBarSearch` shell when themeConfig.search is unset — that is OK.
// Fail only if a functional Search control / index would ship.
{
  const homeHtml = path.join(dist, "index.html");
  if (fs.existsSync(homeHtml)) {
    const home = fs.readFileSync(homeHtml, "utf8");
    const functionalSearch =
      home.includes('id="local-search"') ||
      home.includes("DocSearch-Button") ||
      home.includes("VPLocalSearchBox") ||
      /VPNavBarSearch[\s\S]{0,400}Search/.test(home);
    if (functionalSearch) {
      errors.push(
        "docs search UI present but search is intentionally omitted for v0.2.0 — remove themeConfig.search",
      );
    }
  }
  const chunksDir = path.join(dist, "assets", "chunks");
  if (fs.existsSync(chunksDir)) {
    const chunkNames = fs.readdirSync(chunksDir);
    if (chunkNames.some((n) => n.includes("localSearchIndex"))) {
      errors.push(
        "localSearchIndex chunks present but search is omitted for v0.2.0 — remove themeConfig.search",
      );
    }
  }
}

// Commercial / Platform must not be in active published routes
for (const rel of ["platform/index.html", "community/vs-platform.html"]) {
  if (fs.existsSync(path.join(dist, rel))) {
    errors.push(`commercial/platform route must not be published: ${rel}`);
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
  {
    re: /[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com/i,
    msg: "raw execute-api hostname must not appear in published docs",
  },
];
const contentRoots = [root];
const scanExt = new Set([".md", ".html", ".ts", ".css", ".txt", ".svg", ".mjs", ".json"]);

function shouldScan(file) {
  const rel = path.relative(root, file).replace(/\\/g, "/");
  if (rel.startsWith("node_modules/")) return false;
  if (rel.startsWith(".vitepress/dist/")) return false;
  if (rel.startsWith(".vitepress/cache/")) return false;
  if (rel.startsWith("platform/")) return false;
  if (rel.startsWith("internal/")) return false;
  if (rel === "community/vs-platform.md") return false;
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
    if (href.includes("mailto:")) continue;
    const clean = href.split("#")[0].split("?")[0];
    if (!clean || clean === "/") {
      if (!fs.existsSync(path.join(dist, "index.html"))) {
        errors.push(`broken href ${href} in ${path.relative(dist, file)}`);
      }
      continue;
    }
    if (clean.startsWith("/#")) continue;
    let p = clean;
    if (p.endsWith("/")) p += "index.html";
    else if (!path.extname(p)) p += ".html";
    const candidate = path.join(dist, p.replace(/^\//, ""));
    if (!fs.existsSync(candidate)) {
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

const home = fs.readFileSync(path.join(dist, "index.html"), "utf8");
if (!/CodeStrata/i.test(home)) errors.push("home HTML missing CodeStrata brand");
if (!/Engineering decisions grounded in code/i.test(home)) {
  errors.push("home HTML missing Community Design System tagline");
}
if (/class="name"[^>]*>[\s\S]*?Organizations/i.test(home)) {
  errors.push("home hero title still includes Organizations");
}

const footerMust = [
  "/getting-started/",
  "/reference/cli",
  "/extensions/vscode",
  "/security/privacy",
  "/faq/",
  "https://github.com/CodeStrata/codestrata-engine",
  "https://codestrata.ai/",
];
for (const href of footerMust) {
  if (!home.includes(href)) {
    errors.push(`home footer missing community link: ${href}`);
  }
}
if (home.includes("https://codestrata.ai/platform")) {
  errors.push("footer must not link to codestrata.ai/platform");
}
if (home.includes("/platform/") || home.includes("community/vs-platform")) {
  errors.push("published home must not link to Platform or vs-platform docs");
}
if (!home.includes('class="cs-docs-home"') && !home.includes("cs-docs-home")) {
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
if (!configSrc.includes('logoLink: "/"')) {
  errors.push('config logoLink must be "/" (docs home); Main Site is nav/sidebar');
}
if (!configSrc.includes('link: "https://codestrata.ai/"')) {
  errors.push("config must expose Main Site → https://codestrata.ai/");
}
if (!configSrc.includes("platform/**")) {
  errors.push("config must srcExclude platform/**");
}
if (configSrc.includes('link: "/platform/"')) {
  errors.push("config must not navigate to /platform/");
}
if (/codestrata ai --provider platform/.test(home)) {
  errors.push("published home must not advertise codestrata ai --provider platform");
}

// Design System consumption
const tokensCss = fs.readFileSync(
  path.join(root, ".vitepress/theme/tokens.css"),
  "utf8",
);
if (!tokensCss.includes("design-system/tokens/tokens.css")) {
  errors.push("theme tokens.css must import design-system tokens");
}
if (/--amber:\s*#d98a3d/.test(tokensCss)) {
  errors.push("theme must not re-declare superseded amber palette as authority");
}

console.log(`Scanned ${htmlFiles.length} HTML files in dist`);
for (const w of warnings) console.warn("WARN:", w);
if (errors.length) {
  for (const e of errors) console.error("ERROR:", e);
  console.error(`FAIL: ${errors.length} validation error(s)`);
  process.exit(1);
}
console.log("PASS: documentation validation");
