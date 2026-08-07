/**
 * Slice 13.11 CLI–extension compatibility unit tests.
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  CLI_COMPATIBILITY_POLICY_ID,
  CLI_COMPATIBILITY_POLICY_VERSION,
  COMPATIBILITY_EXTENSION_VERSION,
  COMPATIBILITY_MINIMUM_CLI,
  compatibilityDecisionToStableDict,
  compatibilityDiagnosticsContainForbiddenKeys,
  createCliCompatibilityPolicy,
  cliCompatibilityPolicyToStableDict,
  diagnosticsFromCompatibilityDecision,
  doctorCompatibilityLabel,
  evaluateCliCompatibility,
  cliCompatibilityDiagnosticsToStableDict,
} from "../cliCompatibility";

describe("cli compatibility policy", () => {
  it("serializes as extension 0.2.0 matrix authority", () => {
    const a = cliCompatibilityPolicyToStableDict(createCliCompatibilityPolicy());
    const b = cliCompatibilityPolicyToStableDict(createCliCompatibilityPolicy());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, CLI_COMPATIBILITY_POLICY_ID);
    assert.equal(a.policy_version, CLI_COMPATIBILITY_POLICY_VERSION);
    assert.equal(a.extension_version, COMPATIBILITY_EXTENSION_VERSION);
    assert.equal(a.minimum_cli, COMPATIBILITY_MINIMUM_CLI);
    assert.equal(a.allow_prerelease, false);
    assert.equal(a.compatibility_authority, "extension");
  });
});

describe("compatibility matrix", () => {
  it("supports only CLI 0.2.x", () => {
    assert.equal(
      evaluateCliCompatibility({ cliVersion: "0.2.0" }).verdict,
      "supported"
    );
    assert.equal(
      evaluateCliCompatibility({ cliVersion: "0.2.99" }).supported,
      true
    );
    assert.equal(
      evaluateCliCompatibility({ cliVersion: "0.1.0" }).verdict,
      "upgrade_cli"
    );
    assert.equal(
      evaluateCliCompatibility({ cliVersion: "0.3.0" }).verdict,
      "downgrade_cli"
    );
    assert.equal(
      evaluateCliCompatibility({ cliVersion: "1.0.0" }).verdict,
      "unsupported_major"
    );
    assert.equal(
      evaluateCliCompatibility({ cliVersion: "0.2.0-rc.1" }).verdict,
      "unsupported_prerelease"
    );
    assert.equal(
      evaluateCliCompatibility({ cliVersion: "not-a-version" }).verdict,
      "invalid_version"
    );
    assert.equal(
      evaluateCliCompatibility({ cliVersion: undefined }).verdict,
      "unknown_version"
    );
  });

  it("blocks assessment/telemetry when unsupported", () => {
    const decision = evaluateCliCompatibility({ cliVersion: "0.1.9" });
    assert.equal(decision.assessment_allowed, false);
    assert.equal(decision.workflow_may_continue, false);
    assert.equal(decision.telemetry_allowed, false);
    assert.equal(decision.analytics_allowed, false);
    assert.equal(doctorCompatibilityLabel(decision.verdict), "Upgrade Required");
  });

  it("diagnostics omit forbidden keys", () => {
    const decision = evaluateCliCompatibility({ cliVersion: "0.2.0" });
    const d = cliCompatibilityDiagnosticsToStableDict(
      diagnosticsFromCompatibilityDecision(decision)
    );
    assert.equal(compatibilityDiagnosticsContainForbiddenKeys(d), false);
    assert.equal(d.probe_count, 0);
    assert.equal(
      JSON.stringify(compatibilityDecisionToStableDict(decision)).includes(
        "/Users/"
      ),
      false
    );
  });
});
