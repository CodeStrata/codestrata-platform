/**
 * VS Code anonymous analytics tests (Epic 10 Slice 10.7).
 */

import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as path from "node:path";
import { describe, it } from "node:test";

import {
  APPROVED_ANALYTICS_FIELD_NAMES,
  APPROVED_ANALYTICS_OPERATION_CATEGORIES,
  CaptureVsCodeAnalyticsSink,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_URN,
  COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_URN,
  FORBIDDEN_ANALYTICS_FIELD_NAMES,
  VSCODE_ANALYTICS_CLIENT_NAME,
  allowForSession,
  analyticsEventToStableJson,
  analyticsPolicyToStableJson,
  analyticsPreviewToStableJson,
  analyticsProjectionToStableJson,
  assertVsCodeAnalyticsSchemaCompatible,
  buildVsCodeAnalyticsEvent,
  buildVsCodeAnalyticsPreview,
  classifyDurationBucketMs,
  classifyReleaseAdoption,
  compatibleVsCodeAnalyticsSchemaVersions,
  createIsolationSession,
  defaultConsent,
  defaultUnavailableAnalyticsSink,
  defaultVsCodeAnonymousAnalyticsPolicy,
  denyForSession,
  describeEngineAnalyticsCatalogMapping,
  isolationAnalyticsDiagnostics,
  isAnalyticsConstructionAllowed,
  isEligibleAnalyticsCommand,
  mapCommandIdToAnalyticsOperation,
  nonInteractiveDisabledConsent,
  projectVsCodeAnalyticsEvent,
  projectVsCodeAnalyticsFromMapping,
  runCommandWithTelemetryIsolation,
  validateExtensionVersion,
  validateVsCodeAnalyticsEvent,
  VsCodeAnalyticsError,
} from "../telemetry";

describe("vscode analytics policy/schema", () => {
  it("defines independent policy and schema 1.0", () => {
    const policy = defaultVsCodeAnonymousAnalyticsPolicy();
    assert.equal(policy.policyToken, COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_URN);
    assert.equal(policy.schemaToken, COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_URN);
    assert.equal(policy.persistenceEnabled, false);
    assert.equal(policy.transmissionEnabled, false);
    assert.equal(policy.installationIdentityAllowed, false);
    assert.equal(policy.unavailableSinkDefault, true);
    assert.equal(policy.noHttp, true);
    assert.ok(policy.limitations.includes("identity_free_in_slice_10_7"));
    assert.ok(policy.limitations.includes("cursor_excluded"));
    const json = analyticsPolicyToStableJson(policy);
    assert.equal(json, analyticsPolicyToStableJson(defaultVsCodeAnonymousAnalyticsPolicy()));
    assert.ok(!/"installation_id"\s*:/.test(json));
    assert.ok(!/"machineId"\s*:/.test(json));
    assert.ok(!json.includes("machineId"));
  });

  it("supports only schema 1.0", () => {
    assert.deepEqual(compatibleVsCodeAnalyticsSchemaVersions(), ["1.0"]);
    assertVsCodeAnalyticsSchemaCompatible("1.0");
    assert.throws(
      () => assertVsCodeAnalyticsSchemaCompatible("2.0"),
      (err: unknown) =>
        err instanceof VsCodeAnalyticsError && err.code === "incompatible_schema"
    );
  });
});

describe("vscode analytics consent gating", () => {
  it("reuses command-local consent without a second prompt API", () => {
    assert.equal(isAnalyticsConstructionAllowed(allowForSession()), true);
    assert.equal(isAnalyticsConstructionAllowed(defaultConsent()), false);
    assert.equal(isAnalyticsConstructionAllowed(denyForSession()), false);
    assert.equal(
      isAnalyticsConstructionAllowed(nonInteractiveDisabledConsent()),
      false
    );
  });
});

describe("vscode analytics operation categories", () => {
  it("maps only assess and assess-with-ai", () => {
    assert.deepEqual(
      [...APPROVED_ANALYTICS_OPERATION_CATEGORIES].sort(),
      ["assess", "assess_with_ai"].sort()
    );
    assert.equal(mapCommandIdToAnalyticsOperation("codestrata.assess"), "assess");
    assert.equal(
      mapCommandIdToAnalyticsOperation("codestrata.assessWithAi"),
      "assess_with_ai"
    );
    assert.equal(isEligibleAnalyticsCommand("codestrata.installEngine"), false);
    assert.throws(
      () => mapCommandIdToAnalyticsOperation("codestrata.doctor"),
      (err: unknown) =>
        err instanceof VsCodeAnalyticsError &&
        err.code === "invalid_operation_category"
    );
  });
});

describe("vscode analytics extension version and release adoption", () => {
  it("accepts bounded semver-like versions only", () => {
    assert.equal(validateExtensionVersion("0.2.0"), "0.2.0");
    assert.equal(classifyReleaseAdoption("0.2.0"), "development");
    assert.equal(classifyReleaseAdoption("1.2.3"), "stable");
    assert.equal(classifyReleaseAdoption("1.2.3-beta.1"), "prerelease");
    assert.throws(
      () => validateExtensionVersion("/tmp/ext"),
      (err: unknown) =>
        err instanceof VsCodeAnalyticsError &&
        err.code === "invalid_extension_version"
    );
    assert.throws(() => validateExtensionVersion("not a version!!!"));
  });
});

describe("vscode analytics duration and outcome", () => {
  it("uses coarse buckets only", () => {
    assert.equal(classifyDurationBucketMs(100), "lt_1s");
    assert.equal(classifyDurationBucketMs(5_000), "s_1_10");
    assert.equal(classifyDurationBucketMs(undefined), "unknown");
    assert.equal(classifyDurationBucketMs(Number.NaN), "unknown");
  });

  it("enforces success/failure category consistency", () => {
    assert.throws(
      () =>
        buildVsCodeAnalyticsEvent({
          operationCategory: "assess",
          lifecycle: "feature_completed",
          extensionVersion: "0.2.0",
          releaseAdoption: "development",
          aiUsed: false,
          outcome: "success",
          failureCategory: "command_failed",
        }),
      (err: unknown) =>
        err instanceof VsCodeAnalyticsError &&
        err.code === "outcome_failure_mismatch"
    );
  });
});

describe("vscode analytics AI boolean", () => {
  it("is boolean-only and tied to operation category", () => {
    const ai = buildVsCodeAnalyticsEvent({
      operationCategory: "assess_with_ai",
      lifecycle: "feature_invoked",
      extensionVersion: "0.2.0",
      releaseAdoption: "development",
      aiUsed: true,
    });
    assert.equal(ai.aiUsed, true);
    assert.throws(() =>
      buildVsCodeAnalyticsEvent({
        operationCategory: "assess",
        lifecycle: "feature_invoked",
        extensionVersion: "0.2.0",
        releaseAdoption: "development",
        aiUsed: true,
      })
    );
  });
});

describe("vscode analytics projection/privacy", () => {
  it("projects allowlisted fields only", () => {
    const event = buildVsCodeAnalyticsEvent({
      operationCategory: "assess",
      lifecycle: "feature_completed",
      extensionVersion: "0.2.0",
      releaseAdoption: "development",
      aiUsed: false,
      outcome: "success",
      durationBucket: "s_1_10",
    });
    const projected = projectVsCodeAnalyticsEvent(event);
    assert.equal(projected.fields.client_name, VSCODE_ANALYTICS_CLIENT_NAME);
    assert.ok(!("installation_id" in projected.fields));
    assert.ok(!("machine_id" in projected.fields));
    assert.ok(!("workspace" in projected.fields));
    assert.ok(!("provider" in projected.fields));
    assert.ok(!("model_id" in projected.fields));
    assert.equal(
      analyticsProjectionToStableJson(projected),
      analyticsProjectionToStableJson(projectVsCodeAnalyticsEvent(event))
    );
  });

  it("rejects forbidden fields structurally", () => {
    for (const field of [
      "installation_id",
      "machineId",
      "workspace_uri",
      "repository",
      "document_uri",
      "argv",
      "stdout",
      "finding",
      "prompt",
      "provider",
      "model_id",
      "token_count",
      "cost",
      "raw_command_id",
    ]) {
      assert.ok(!(APPROVED_ANALYTICS_FIELD_NAMES as readonly string[]).includes(field));
      assert.ok((FORBIDDEN_ANALYTICS_FIELD_NAMES as readonly string[]).includes(field));
      assert.throws(
        () => projectVsCodeAnalyticsFromMapping({ [field]: "x" }),
        (err: unknown) =>
          err instanceof VsCodeAnalyticsError &&
          (err.code === "privacy_rejected" || err.code === "unknown_field")
      );
    }
  });
});

describe("vscode analytics preview", () => {
  it("is local, deterministic, and identity-free", () => {
    const a = buildVsCodeAnalyticsPreview({ extensionVersion: "0.2.0" });
    const b = buildVsCodeAnalyticsPreview({ extensionVersion: "0.2.0" });
    assert.equal(a.transmissionPerformed, false);
    assert.equal(a.persistencePerformed, false);
    assert.equal(a.identityPresent, false);
    assert.equal(analyticsPreviewToStableJson(a), analyticsPreviewToStableJson(b));
    assert.ok(!analyticsPreviewToStableJson(a).includes("installation_id"));
  });
});

describe("vscode analytics sink", () => {
  it("defaults to unavailable and never claims sent", () => {
    const sink = defaultUnavailableAnalyticsSink();
    const event = buildVsCodeAnalyticsEvent({
      operationCategory: "assess",
      lifecycle: "feature_invoked",
      extensionVersion: "0.2.0",
      releaseAdoption: "development",
      aiUsed: false,
    });
    const result = sink.send(projectVsCodeAnalyticsEvent(event));
    assert.equal(result.kind, "unavailable");
    assert.equal(sink.sinkCategory, "unavailable");
  });
});

describe("vscode analytics command isolation", () => {
  it("constructs analytics only when consent allows", async () => {
    const capture = new CaptureVsCodeAnalyticsSink();
    const allowed = createIsolationSession({
      consent: allowForSession(),
      analyticsSink: capture,
      extensionVersion: "0.2.0",
      nowMs: (() => {
        let t = 0;
        return () => {
          t += 2_500;
          return t;
        };
      })(),
    });
    const value = await runCommandWithTelemetryIsolation({
      session: allowed,
      aiUsed: false,
      primary: async () => "success" as const,
    });
    assert.equal(value, "success");
    assert.ok(capture.captured.length >= 2);
    assert.equal(capture.captured[0]?.fields.operation_category, "assess");
    assert.equal(capture.captured[0]?.fields.ai_used, false);
    assert.ok(!("installation_id" in (capture.captured[0]?.fields ?? {})));

    const deniedCapture = new CaptureVsCodeAnalyticsSink();
    const denied = createIsolationSession({
      consent: denyForSession(),
      analyticsSink: deniedCapture,
      extensionVersion: "0.2.0",
    });
    await runCommandWithTelemetryIsolation({
      session: denied,
      aiUsed: true,
      primary: async () => "done",
    });
    assert.equal(deniedCapture.captured.length, 0);
    assert.ok(isolationAnalyticsDiagnostics(denied).rejected >= 1);
  });

  it("preserves primary failure when analytics sink raises", async () => {
    const capture = new CaptureVsCodeAnalyticsSink("captured", true);
    const session = createIsolationSession({
      consent: allowForSession(),
      analyticsSink: capture,
      extensionVersion: "0.2.0",
    });
    await assert.rejects(
      () =>
        runCommandWithTelemetryIsolation({
          session,
          aiUsed: true,
          primary: async () => {
            throw new Error("primary_command_failed");
          },
        }),
      /primary_command_failed/
    );
  });

  it("sets assess_with_ai and aiUsed for AI path", async () => {
    const capture = new CaptureVsCodeAnalyticsSink();
    const session = createIsolationSession({
      consent: allowForSession(),
      analyticsSink: capture,
      extensionVersion: "0.2.0",
    });
    await runCommandWithTelemetryIsolation({
      session,
      aiUsed: true,
      primary: async () => "success" as const,
    });
    assert.equal(capture.captured[0]?.fields.operation_category, "assess_with_ai");
    assert.equal(capture.captured[0]?.fields.ai_used, true);
    assert.ok(!("provider" in (capture.captured[0]?.fields ?? {})));
    assert.ok(!("model_id" in (capture.captured[0]?.fields ?? {})));
  });
});

describe("vscode analytics diagnostics", () => {
  it("omits identity and path-like values", async () => {
    const session = createIsolationSession({
      consent: allowForSession(),
      extensionVersion: "0.2.0",
    });
    await runCommandWithTelemetryIsolation({
      session,
      aiUsed: false,
      primary: async () => "ok",
    });
    const diag = isolationAnalyticsDiagnostics(session);
    assert.ok(!("installation_id" in diag));
    assert.ok(!("machineId" in diag));
    assert.ok(!("workspace" in diag));
    const blob = JSON.stringify(diag);
    for (const needle of [
      '"installation_id"',
      "machineId",
      "/Users/",
      "Authorization",
      "file://",
    ]) {
      assert.ok(!blob.includes(needle), needle);
    }
  });
});
describe("vscode analytics determinism", () => {
  it("produces identical stable JSON for equivalent inputs", () => {
    const a = buildVsCodeAnalyticsEvent({
      operationCategory: "assess",
      lifecycle: "feature_invoked",
      extensionVersion: "0.2.0",
      releaseAdoption: "development",
      aiUsed: false,
    });
    const b = buildVsCodeAnalyticsEvent({
      operationCategory: "assess",
      lifecycle: "feature_invoked",
      extensionVersion: "0.2.0",
      releaseAdoption: "development",
      aiUsed: false,
    });
    assert.equal(analyticsEventToStableJson(a), analyticsEventToStableJson(b));
    assert.equal(
      JSON.stringify(validateVsCodeAnalyticsEvent(a).fields),
      JSON.stringify(validateVsCodeAnalyticsEvent(b).fields)
    );
  });
});

describe("vscode analytics no network", () => {
  it("analytics modules do not reference HTTP clients or endpoints", () => {
    const root = path.resolve(__dirname, "../telemetry/analytics");
    for (const file of fs.readdirSync(root)) {
      if (!file.endsWith(".ts") && !file.endsWith(".js")) {
        continue;
      }
      const text = fs.readFileSync(path.join(root, file), "utf8");
      assert.ok(!/\bfetch\s*\(/.test(text));
      assert.ok(!text.includes("node:http"));
      assert.ok(!text.includes("node:https"));
      assert.ok(!text.includes("axios"));
      assert.ok(!text.includes("undici"));
      assert.ok(!/https?:\/\//.test(text));
    }
    const event = buildVsCodeAnalyticsEvent({
      operationCategory: "assess",
      lifecycle: "feature_invoked",
      extensionVersion: "0.2.0",
      releaseAdoption: "development",
      aiUsed: false,
    });
    const projected = projectVsCodeAnalyticsEvent(event);
    assert.equal(
      defaultUnavailableAnalyticsSink().send(projected).kind,
      "unavailable"
    );
  });
});

describe("vscode analytics package and boundary", () => {
  it("does not add analytics settings or telemetry endpoint settings to package.json", () => {
    const pkg = JSON.parse(
      fs.readFileSync(path.resolve(__dirname, "../../package.json"), "utf8")
    ) as {
      version: string;
      contributes: {
        commands: Array<{ command: string }>;
        configuration?: { properties?: Record<string, unknown> };
      };
    };
    assert.equal(pkg.version, "0.2.0");
    const commands = pkg.contributes.commands.map((c) => c.command);
    assert.ok(!commands.some((c) => /analytics/i.test(c)));
    assert.ok(commands.includes("codestrata.telemetrySettings"));
    const props = Object.keys(pkg.contributes.configuration?.properties ?? {});
    assert.ok(!props.some((p) => /analytics/i.test(p)));
    assert.ok(!props.some((p) => /telemetry/i.test(p)));
    assert.ok(!props.some((p) => /endpoint/i.test(p)));
    assert.ok(!props.some((p) => /installation.?id/i.test(p)));
  });

  it("does not import Platform, Data Lake, Engine Python, or Cursor", () => {
    const root = path.resolve(__dirname, "../telemetry/analytics");
    for (const file of fs.readdirSync(root)) {
      if (!file.endsWith(".ts")) {
        continue;
      }
      const text = fs.readFileSync(path.join(root, file), "utf8");
      assert.ok(!text.includes("codestrata_platform"));
      assert.ok(!text.includes("boto3"));
      assert.ok(!text.includes("@aws-sdk"));
      assert.ok(!text.includes("cursor-plugin"));
      assert.ok(!text.includes("codestrata.telemetry.analytics"));
      assert.ok(!/from ["']codestrata/.test(text));
      assert.ok(!text.includes("vscode.env.machineId"));
      assert.ok(!text.includes("telemetrySessionId"));
      assert.ok(!text.includes("anonymous-installation-identity"));
    }
  });

  it("does not change Cursor plugin sources", () => {
    const cursor = path.resolve(__dirname, "../../../cursor-plugin/src");
    if (!fs.existsSync(cursor)) {
      return;
    }
    const hits: string[] = [];
    const walk = (dir: string) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          walk(full);
          continue;
        }
        if (entry.name.includes("analytics") || entry.name.includes("telemetry")) {
          hits.push(full);
        }
      }
    };
    walk(cursor);
    assert.deepEqual(hits, []);
  });

  it("documents conceptual Engine differences without schema equality", () => {
    const note = describeEngineAnalyticsCatalogMapping();
    assert.equal(note.schemasIdentical, false);
    assert.equal(note.vscodeIdentityFreeInSlice107, true);
    assert.equal(note.vscodeCollectsProviderModel, false);
    assert.equal(note.vscodeHttpTransport, "unavailable");
  });
});
