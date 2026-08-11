#!/usr/bin/env node
/**
 * Regenerate docs/security/collected-fields.md from Slice 18.1 field register.
 * Run from docs/: node scripts/generate-collected-fields.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const docsRoot = resolve(__dirname, "..");
const monorepo = resolve(docsRoot, "..");
const registerPath = join(
  monorepo,
  "platform/policies/community_telemetry_field_register.json",
);
const outPath = join(docsRoot, "security/collected-fields.md");

const register = JSON.parse(readFileSync(registerPath, "utf8"));
const entries = register.entries || [];
const byRoute = new Map();
for (const e of entries) {
  const key = e.api_route || "unknown";
  if (!byRoute.has(key)) byRoute.set(key, []);
  byRoute.get(key).push(e);
}

const titles = {
  "POST /api/v1/telemetry": "Product telemetry",
  "POST /api/v1/assessment-metadata": "Assessment metadata",
  "POST /api/v1/cli-events": "CLI events",
  "POST /api/v1/extension-events": "Extension events",
  "POST /api/v1/ai-usage": "AI usage metadata",
  "POST /api/v1/reports/upload-intents": "Report upload intents",
  "POST /api/v1/reports": "Report publish",
};

let body = `---
title: Collected Fields
description: Developer field reference for Community Cloud ingestion and report-publish APIs, generated from Slice 18.1 runtime inventory.
---

# Collected Fields

This page is generated from the authoritative Slice 18.1 register
\`community-telemetry-field-register:1.0\` (runtime pydantic models).

**Field count:** ${register.field_count || entries.length}

Do not treat every event below as actively emitted by the current Engine
assess path. See [Data Collection](/security/data-collection) for honest
producer status.

Related: [Telemetry](/reference/telemetry) · [Privacy](/security/privacy) ·
[Community Cloud API](/reference/community-api/)

`;

for (const [route, fields] of byRoute) {
  const title = titles[route] || route;
  const dest = fields[0]?.stored_destination || "n/a";
  const retention = fields[0]?.retention || "n/a";
  body += `## ${title} (\`${route}\`)\n\n`;
  body += `API route: \`${route}\` · Destination: \`${dest}\` · Retention class: \`${retention}\`\n\n`;
  body += `| Field | Type | Required | Privacy classification | Insights? |\n`;
  body += `| --- | --- | --- | --- | --- |\n`;
  const sorted = [...fields].sort((a, b) =>
    String(a.field_name).localeCompare(String(b.field_name)),
  );
  for (const f of sorted) {
    const insights = f.shown_in_insights ? "yes" : "no";
    body += `| \`${f.field_name}\` | \`${f.type}\` | ${f.required} | ${f.privacy_classification} | ${insights} |\n`;
  }
  body += `\n`;
}

writeFileSync(outPath, body, "utf8");
console.log(`Wrote ${outPath} fields=${entries.length}`);
