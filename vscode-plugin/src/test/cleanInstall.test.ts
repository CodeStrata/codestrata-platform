/**
 * Clean-install policy unit tests (Slice 13.14).
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  createCleanInstallPolicy,
  cleanInstallPolicyToStableDict,
  STABLE_COMMAND_IDS,
  STABLE_SETTING_KEYS,
  FORBIDDEN_PERSISTED_STATE_KEYS,
} from "../cleanInstall";

describe("clean install policy", () => {
  it("serializes deterministically without paths or timestamps", () => {
    const a = cleanInstallPolicyToStableDict(createCleanInstallPolicy());
    const b = cleanInstallPolicyToStableDict(createCleanInstallPolicy());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.extension_version, "0.2.1");
    assert.equal(a.supported_cli_family, "0.2.x");
    assert.equal(a.marketplace_publish_required, false);
    assert.equal(a.automatic_cli_install_allowed, false);
    assert.equal(a.machine_identity_allowed, false);
    const blob = JSON.stringify(a);
    assert.ok(!blob.includes("timestamp"));
    assert.ok(!blob.includes("/Users/"));
  });

  it("lists stable settings and forbids installation identity keys", () => {
    assert.ok(STABLE_SETTING_KEYS.includes("codestrata.engine.executable"));
    assert.ok(STABLE_COMMAND_IDS.includes("codestrata.assess"));
    assert.ok(
      FORBIDDEN_PERSISTED_STATE_KEYS.some((k) => k.includes("installationId"))
    );
    assert.ok(
      !FORBIDDEN_PERSISTED_STATE_KEYS.includes("codestrata.telemetryPreference")
    );
  });
});
