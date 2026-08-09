/**
 * Slice 14.12 — documentation deployment preflight.
 *
 * Validates checked-in Wrangler config, local Wrangler dependency, and exact
 * alignment between VitePress output and assets.directory. Never deploys.
 *
 * Exit 0 on success. Exit 1 on contract failure. Prints relative paths only.
 */
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, normalize, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, "..");
const WRANGLER_CONFIG = join(PACKAGE_ROOT, "wrangler.jsonc");
const PACKAGE_JSON = join(PACKAGE_ROOT, "package.json");
const LOCKFILE = join(PACKAGE_ROOT, "package-lock.json");
const VITEPRESS_OUT = join(PACKAGE_ROOT, ".vitepress", "dist");

const FORBIDDEN_DIST_FRAGMENTS = [
  "/platform/",
  "/data-lake/",
  "/community-cloud/",
  "/enterprise/",
  "/commercial/",
  "/internal/",
  "/product-discovery/",
];

const errors = [];
const notes = [];

function fail(message) {
  errors.push(message);
}

function readJsonc(path) {
  const raw = readFileSync(path, "utf8");
  // Strip // line comments and /* */ blocks for the small checked-in config.
  const stripped = raw
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");
  return JSON.parse(stripped);
}

function assertRelativeUnderPackage(absPath, label) {
  const rel = relative(PACKAGE_ROOT, absPath);
  if (rel.startsWith("..") || rel.includes(`..${sep}`)) {
    fail(`${label} escapes package root: ${rel}`);
  }
  return rel.split(sep).join("/");
}

// 1. Checked-in Wrangler config
if (!existsSync(WRANGLER_CONFIG)) {
  fail("wrangler.jsonc missing (checked-in config required)");
}

let config = null;
if (existsSync(WRANGLER_CONFIG)) {
  try {
    config = readJsonc(WRANGLER_CONFIG);
  } catch (error) {
    fail(`wrangler.jsonc parse failed: ${error.name || "Error"}`);
  }
}

// 2. Local Wrangler package (never npx dynamic install)
const require = createRequire(import.meta.url);
let wranglerPkg = null;
try {
  const wranglerPackageJson = require.resolve("wrangler/package.json", {
    paths: [PACKAGE_ROOT],
  });
  wranglerPkg = JSON.parse(readFileSync(wranglerPackageJson, "utf8"));
  notes.push(`local_wrangler=${wranglerPkg.version}`);
} catch {
  fail("local wrangler package missing — add wrangler as a docs dependency");
}

// 3–5. assets.directory alignment
if (config) {
  if (config.main) {
    fail("Worker main entrypoint must not be required for static docs");
  }
  const flags = config.compatibility_flags || [];
  if (flags.includes("nodejs_compat")) {
    fail("nodejs_compat enabled without static-docs requirement");
  }
  if (!config.compatibility_date || typeof config.compatibility_date !== "string") {
    fail("compatibility_date must be an intentional checked-in string");
  }
  const directory = config.assets?.directory;
  if (!directory || typeof directory !== "string") {
    fail("assets.directory missing");
  } else {
    const normalized = normalize(directory).replace(/\\/g, "/");
    if (
      normalized === "docs/.vitepress/dist" ||
      normalized === "./docs/.vitepress/dist" ||
      normalized.endsWith("/docs/.vitepress/dist")
    ) {
      fail(
        "assets.directory uses monorepo-relative docs/.vitepress/dist — use ./.vitepress/dist relative to the docs package root (v0.1.0 failure class)",
      );
    }
    const resolvedAssets = resolve(PACKAGE_ROOT, directory);
    const assetsRel = assertRelativeUnderPackage(resolvedAssets, "assets.directory");
    const vitepressRel = assertRelativeUnderPackage(VITEPRESS_OUT, "vitepress_out");
    if (assetsRel !== vitepressRel) {
      fail(
        `output alignment mismatch: vitepress=${vitepressRel} assets.directory=${assetsRel}`,
      );
    } else {
      notes.push(`aligned_output=${assetsRel}`);
    }
    if (!existsSync(resolvedAssets) || !statSync(resolvedAssets).isDirectory()) {
      fail(`output directory missing: ${assetsRel} (run npm run build first)`);
    } else {
      const indexPath = join(resolvedAssets, "index.html");
      if (!existsSync(indexPath)) {
        fail("index.html missing in build output");
      }
      const assetsDir = join(resolvedAssets, "assets");
      if (!existsSync(assetsDir) || !statSync(assetsDir).isDirectory()) {
        fail("VitePress assets/ directory missing in build output");
      }
      if (!existsSync(join(resolvedAssets, "sitemap.xml"))) {
        fail("sitemap.xml missing in build output");
      }
      if (!existsSync(join(resolvedAssets, "favicon.ico"))) {
        fail("favicon.ico missing in build output");
      }
      if (!existsSync(join(resolvedAssets, "favicon.png"))) {
        fail("favicon.png missing in build output");
      }
      if (!existsSync(join(resolvedAssets, "apple-touch-icon.png"))) {
        fail("apple-touch-icon.png missing in build output");
      }
      for (const brand of [
        "brand/lockup-horizontal-on-light.svg",
        "brand/lockup-horizontal-on-dark.svg",
        "brand/icon.svg",
      ]) {
        if (!existsSync(join(resolvedAssets, brand))) {
          fail(`brand asset missing in build output: ${brand}`);
        }
      }

      // Community publish scope — sample generated HTML + sitemap.
      const sitemap = readFileSync(join(resolvedAssets, "sitemap.xml"), "utf8");
      for (const fragment of FORBIDDEN_DIST_FRAGMENTS) {
        if (sitemap.includes(fragment)) {
          fail(`sitemap exposes excluded content: ${fragment}`);
        }
      }
      const walkHtml = (dir, depth = 0) => {
        if (depth > 4) return;
        for (const entry of readdirSync(dir, { withFileTypes: true })) {
          const full = join(dir, entry.name);
          if (entry.isDirectory()) {
            if (entry.name === "assets" || entry.name === "fonts") continue;
            walkHtml(full, depth + 1);
          } else if (entry.name.endsWith(".html")) {
            const rel = relative(resolvedAssets, full).split(sep).join("/");
            for (const fragment of [
              "platform/",
              "data-lake/",
              "community/vs-platform",
            ]) {
              if (rel.includes(fragment)) {
                fail(`excluded page present in dist: ${rel}`);
              }
            }
          }
        }
      };
      walkHtml(resolvedAssets);
    }
  }
}

// package metadata
if (!existsSync(PACKAGE_JSON) || !existsSync(LOCKFILE)) {
  fail("package.json / package-lock.json required for npm ci");
} else {
  const pkg = JSON.parse(readFileSync(PACKAGE_JSON, "utf8"));
  if (!pkg.devDependencies?.wrangler && !pkg.dependencies?.wrangler) {
    fail("wrangler must be declared in package.json dependencies");
  }
  if (typeof pkg.scripts?.build !== "string" || !pkg.scripts.build.includes("vitepress")) {
    fail("build script must be VitePress-only");
  }
  if (
    typeof pkg.scripts?.["deploy:upload"] === "string" &&
    /\bbuild\b/.test(pkg.scripts["deploy:upload"])
  ) {
    fail("deploy:upload must not invoke build (build-once / Approach A)");
  }
  if (
    typeof pkg.scripts?.deploy === "string" &&
    pkg.scripts.deploy.includes("npm run build")
  ) {
    fail("deploy must not build — use deploy:local for operator convenience");
  }
}

if (errors.length) {
  console.error(
    JSON.stringify(
      {
        ok: false,
        package_root: "docs",
        errors,
        notes,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}

console.log(
  JSON.stringify(
    {
      ok: true,
      package_root: "docs",
      wrangler_config: "wrangler.jsonc",
      assets_directory: "./.vitepress/dist",
      vitepress_output: ".vitepress/dist",
      notes,
    },
    null,
    2,
  ),
);
