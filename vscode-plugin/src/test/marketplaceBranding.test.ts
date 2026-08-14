/**
 * Marketplace branding unit tests (Slice 13.12).
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import fs from "node:fs";
import path from "node:path";
import {
  createMarketplaceBrandingPolicy,
  marketplaceBrandingPolicyToStableDict,
  MARKETPLACE_DISPLAY_NAME,
  MARKETPLACE_GALLERY_BANNER_COLOR,
  MARKETPLACE_GALLERY_ORDER,
  MARKETPLACE_PUBLISHER_NAME,
  marketplaceTextContainsForbiddenClaim,
} from "../marketplaceBranding";

describe("marketplace branding policy", () => {
  it("serializes deterministically without timestamps", () => {
    const a = marketplaceBrandingPolicyToStableDict(
      createMarketplaceBrandingPolicy()
    );
    const b = marketplaceBrandingPolicyToStableDict(
      createMarketplaceBrandingPolicy()
    );
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.extension_version, "0.2.2");
    assert.equal(a.display_name, MARKETPLACE_DISPLAY_NAME);
    assert.equal(a.publisher_name, "CodeStrataAI");
    assert.equal(a.publisher_name, MARKETPLACE_PUBLISHER_NAME);
    assert.equal(a.gallery_banner_color, MARKETPLACE_GALLERY_BANNER_COLOR);
    assert.equal(a.visual_reference, "current_codestrata_website");
    assert.equal(a.cursor_branding_allowed, false);
    const blob = JSON.stringify(a);
    assert.ok(!blob.includes("timestamp"));
    assert.ok(!blob.includes("/Users/"));
  });
});

describe("package.json marketplace identity", () => {
  it("declares publisher CodeStrataAI and extension id CodeStrataAI.codestrata-assessment", () => {
    const pkg = JSON.parse(
      fs.readFileSync(path.resolve(__dirname, "../../package.json"), "utf8")
    ) as { publisher: string; name: string; version: string };
    assert.equal(pkg.publisher, "CodeStrataAI");
    assert.equal(pkg.publisher, MARKETPLACE_PUBLISHER_NAME);
    assert.equal(pkg.name, "codestrata-assessment");
    assert.equal(pkg.version, "0.2.2");
    assert.equal(`${pkg.publisher}.${pkg.name}`, "CodeStrataAI.codestrata-assessment");
  });
});

describe("gallery order", () => {
  it("lists five deterministic screenshots", () => {
    assert.equal(MARKETPLACE_GALLERY_ORDER.length, 5);
    assert.equal(MARKETPLACE_GALLERY_ORDER[0], "media/screenshot-assessment.png");
    assert.equal(MARKETPLACE_GALLERY_ORDER[1], "media/screenshot-report.png");
    assert.equal(MARKETPLACE_GALLERY_ORDER[4], "media/screenshot-ai-assessment.png");
  });
});

describe("readme marketplace screenshots", () => {
  it("uses public HTTPS screenshot URLs without a private repository host", () => {
    const readme = fs.readFileSync(
      path.resolve(__dirname, "../../README.md"),
      "utf8"
    );
    const base = "https://docs.codestrata.ai/media/vscode-marketplace/";
    for (const name of [
      "screenshot-assessment.png",
      "screenshot-report.png",
      "screenshot-progress.png",
      "screenshot-initialization.png",
      "screenshot-ai-assessment.png",
    ]) {
      assert.ok(readme.includes(`${base}${name}`), name);
    }
    assert.equal(readme.includes("github.com/"), false);
    assert.equal(/\((media\/screenshot-[^)]+)\)/.test(readme), false);
  });
});

describe("claims", () => {
  it("rejects unsupported Marketplace claims", () => {
    assert.equal(
      marketplaceTextContainsForbiddenClaim("supports Cursor workflows"),
      true
    );
    assert.equal(
      marketplaceTextContainsForbiddenClaim("all source always stays local"),
      true
    );
    assert.equal(
      marketplaceTextContainsForbiddenClaim(
        "Engineering decisions grounded in code."
      ),
      false
    );
  });
});
