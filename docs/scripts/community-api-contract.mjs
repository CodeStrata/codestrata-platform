#!/usr/bin/env node
/**
 * Schema-driven Community API docs contract checks (Slice 17.14 / reconciled 18.5).
 *
 * Validates docs/reference/community-api/index.md against
 * platform/policies/community_api_route_register.json without inventing routes.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "../..");
const docsPage = path.join(root, "docs/reference/community-api/index.md");
const registerPath = path.join(
  root,
  "platform/policies/community_api_route_register.json",
);

const errors = [];
const PUBLIC_BASE = "https://api.codestrata.ai";

const register = JSON.parse(fs.readFileSync(registerPath, "utf8"));
const docs = fs.readFileSync(docsPage, "utf8");

if (register.schema !== "community-api-route-register:1.0") {
  errors.push(`unexpected register schema: ${register.schema}`);
}
if (register.public_api_base_url !== PUBLIC_BASE) {
  errors.push(`register base URL mismatch: ${register.public_api_base_url}`);
}

const classifications = new Set([
  "PUBLIC_COMMUNITY",
  "AUTHENTICATED_COMMUNITY_INGESTION",
  "AUTHENTICATED_REPORT_PUBLISHING",
  "PRIVATE_INSIGHTS",
  "INTERNAL_OPERATIONAL",
  "DEPRECATED",
]);

const DOCUMENTED_COMMUNITY = new Set([
  "PUBLIC_COMMUNITY",
  "AUTHENTICATED_COMMUNITY_INGESTION",
  "AUTHENTICATED_REPORT_PUBLISHING",
]);

function docsContainUrl(publicPath) {
  const canonical = `${PUBLIC_BASE}${publicPath}`;
  if (docs.includes(canonical)) return true;
  // Accept angle-bracket placeholder docs form for path params.
  const angled = canonical.replaceAll("{public_id}", "<public-id>");
  return docs.includes(angled);
}

const publicRoutes = [];
const documentedCommunity = [];
for (const route of register.routes || []) {
  if (!classifications.has(route.classification)) {
    errors.push(`unclassified route: ${route.route_id}`);
  }
  if (route.community_visible) {
    documentedCommunity.push(route);
    if (!DOCUMENTED_COMMUNITY.has(route.classification)) {
      errors.push(
        `community_visible with unexpected classification: ${route.route_id} (${route.classification})`,
      );
    }
    if (route.classification === "PUBLIC_COMMUNITY") {
      publicRoutes.push(route);
    }
    if (!docsContainUrl(route.public_path)) {
      errors.push(
        `docs missing canonical URL for ${route.route_id}: ${PUBLIC_BASE}${route.public_path}`,
      );
    }
    if (!docs.includes(route.method)) {
      errors.push(`docs missing method for ${route.route_id}`);
    }
  } else if (route.classification === "PRIVATE_INSIGHTS") {
    const url = `${PUBLIC_BASE}${route.public_path}`;
    if (docs.includes(url)) {
      errors.push(`private Insights route documented as Community API: ${route.public_path}`);
    }
  }
}

const requiredTransparency = [
  "source code",
  "repository file paths",
  "assessment findings",
  "prompts",
  "API keys",
  "machineId",
];
for (const phrase of requiredTransparency) {
  if (!docs.toLowerCase().includes(phrase.toLowerCase())) {
    errors.push(`docs missing transparency phrase: ${phrase}`);
  }
}

if (/\b[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com\b/i.test(docs)) {
  errors.push("docs advertise execute-api hostname");
}

if (!docs.includes("Developers can inspect CodeStrata network requests")) {
  errors.push("docs missing transparency inspection statement");
}

if (publicRoutes.length < 3) {
  errors.push(`expected >=3 public community routes, got ${publicRoutes.length}`);
}
if (documentedCommunity.length < 6) {
  errors.push(
    `expected >=6 community-documented routes, got ${documentedCommunity.length}`,
  );
}

if (errors.length) {
  console.error("FAIL community-api-contract:");
  for (const e of errors) console.error(` - ${e}`);
  process.exit(1);
}

console.log(
  `OK community-api-contract public_routes=${publicRoutes.length} documented_community=${documentedCommunity.length} private_excluded=ok`,
);
