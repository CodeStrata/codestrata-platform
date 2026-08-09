/**
 * Insights Cloudflare deploy preflight (Slice 17.8).
 * Validates checked-in Wrangler config and local wrangler dependency. Never deploys.
 */
import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, normalize, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, "..");
const WRANGLER_CONFIG = join(PACKAGE_ROOT, "wrangler.jsonc");
const PACKAGE_JSON = join(PACKAGE_ROOT, "package.json");
const errors = [];
const notes = [];

function fail(message) {
  errors.push(message);
}

function readJsonc(path) {
  const raw = readFileSync(path, "utf8");
  const stripped = raw
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");
  return JSON.parse(stripped);
}

if (!existsSync(WRANGLER_CONFIG)) {
  fail("wrangler.jsonc missing");
}

let config = null;
if (existsSync(WRANGLER_CONFIG)) {
  try {
    config = readJsonc(WRANGLER_CONFIG);
  } catch (error) {
    fail(`wrangler.jsonc parse failed: ${error.name || "Error"}`);
  }
}

const require = createRequire(import.meta.url);
try {
  const wranglerPackageJson = require.resolve("wrangler/package.json", {
    paths: [PACKAGE_ROOT],
  });
  const wranglerPkg = JSON.parse(readFileSync(wranglerPackageJson, "utf8"));
  notes.push(`local_wrangler=${wranglerPkg.version}`);
} catch {
  fail("local wrangler package missing — add wrangler as an insights dependency");
}

const pkg = JSON.parse(readFileSync(PACKAGE_JSON, "utf8"));
if (!pkg.devDependencies?.wrangler && !pkg.dependencies?.wrangler) {
  fail("wrangler must be declared in package.json dependencies");
}

if (config) {
  if (config.name !== "codestrata-insights") {
    fail("wrangler name must be codestrata-insights");
  }
  const directory = config.assets?.directory;
  if (!directory || typeof directory !== "string") {
    fail("assets.directory missing");
  } else {
    const normalized = normalize(directory).replace(/\\/g, "/");
    if (normalized === "insights/dist" || normalized.includes("insights/")) {
      fail("assets.directory must be package-relative ./dist (not monorepo path)");
    }
    if (normalized !== "dist" && normalized !== "./dist") {
      fail(`assets.directory must be ./dist (got ${normalized})`);
    }
  }
  if (config.assets?.not_found_handling !== "single-page-application") {
    fail("assets.not_found_handling must be single-page-application");
  }
  if (!config.main) {
    fail("worker main required for same-origin /api proxy");
  }
  const relMain = relative(PACKAGE_ROOT, resolve(PACKAGE_ROOT, config.main));
  if (relMain.startsWith("..") || relMain.includes(`..${sep}`)) {
    fail("worker main escapes package root");
  }
  if (!existsSync(resolve(PACKAGE_ROOT, config.main))) {
    fail("worker main file missing");
  }
  if (!config.vars?.UPSTREAM_API_BASE) {
    fail("vars.UPSTREAM_API_BASE required for API proxy");
  }
  if (/cloudflare|api.?token|secret/i.test(JSON.stringify(config))) {
    // structural presence of secret-like keys beyond UPSTREAM is rejected below
  }
  for (const key of Object.keys(config)) {
    if (/token|secret|password|credential/i.test(key)) {
      fail(`forbidden wrangler key: ${key}`);
    }
  }
}

if (errors.length) {
  console.error(JSON.stringify({ ok: false, errors, notes }, null, 2));
  process.exit(1);
}

console.log(
  JSON.stringify(
    {
      ok: true,
      package_root: "insights",
      wrangler_config: "wrangler.jsonc",
      assets_directory: "./dist",
      notes,
    },
    null,
    2,
  ),
);
