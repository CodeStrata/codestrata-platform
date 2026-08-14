/**
 * Marketplace documentation unit tests (Slice 13.13).
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import {
  createMarketplaceDocsPolicy,
  marketplaceDocsPolicyToStableDict,
  MARKETPLACE_README_REQUIRED_HEADINGS,
  marketplaceDocsContainForbiddenClaim,
  marketplaceListingContainsInternalLeak,
  marketplaceClaimMatrixToStableDict,
} from "../marketplaceDocs";

describe("marketplace docs policy", () => {
  it("serializes deterministically", () => {
    const a = marketplaceDocsPolicyToStableDict(createMarketplaceDocsPolicy());
    const b = marketplaceDocsPolicyToStableDict(createMarketplaceDocsPolicy());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.extension_version, "0.2.2");
    assert.equal(a.listing_authority, "readme");
    assert.equal(a.telemetry_operational_claim_allowed, false);
    assert.equal(a.clean_install_validation_complete, true);
  });
});

describe("claim matrix", () => {
  it("is stable and marks Cursor prohibited", () => {
    const dict = marketplaceClaimMatrixToStableDict();
    assert.equal(
      JSON.stringify(dict),
      JSON.stringify(marketplaceClaimMatrixToStableDict())
    );
    const claims = dict.claims as Array<{
      topic: string;
      classification: string;
    }>;
    const cursor = claims.find((c) => c.topic === "cursor_support");
    assert.equal(cursor?.classification, "prohibited_claim");
  });
});

describe("readme listing", () => {
  it("has required headings and no internal leaks", () => {
    const readme = fs.readFileSync(
      path.resolve(__dirname, "../../README.md"),
      "utf8"
    );
    for (const heading of MARKETPLACE_README_REQUIRED_HEADINGS) {
      assert.ok(readme.includes(`## ${heading}`), heading);
    }
    assert.equal(marketplaceListingContainsInternalLeak(readme), false);
    assert.equal(marketplaceDocsContainForbiddenClaim(readme), false);
    assert.ok(readme.includes("0.2.x"));
    assert.ok(
      readme.includes(
        "The VS Code extension does not directly send repository source to AI providers."
      )
    );
  });
});
