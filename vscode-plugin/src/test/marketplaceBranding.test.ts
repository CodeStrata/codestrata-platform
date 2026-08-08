/**
 * Marketplace branding unit tests (Slice 13.12).
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  createMarketplaceBrandingPolicy,
  marketplaceBrandingPolicyToStableDict,
  MARKETPLACE_DISPLAY_NAME,
  MARKETPLACE_GALLERY_BANNER_COLOR,
  MARKETPLACE_GALLERY_ORDER,
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
    assert.equal(a.extension_version, "0.2.0");
    assert.equal(a.display_name, MARKETPLACE_DISPLAY_NAME);
    assert.equal(a.gallery_banner_color, MARKETPLACE_GALLERY_BANNER_COLOR);
    assert.equal(a.visual_reference, "current_codestrata_website");
    assert.equal(a.cursor_branding_allowed, false);
    const blob = JSON.stringify(a);
    assert.ok(!blob.includes("timestamp"));
    assert.ok(!blob.includes("/Users/"));
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
