/**
 * VS Code telemetry runtime unit tests (Slice 9.13).
 */

import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as path from "node:path";
import { describe, it } from "node:test";

import {
  CaptureExtensionTelemetryTransport,
  COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_URN,
  VSCODE_CLIENT_NAME,
  allowForSession,
  buildVsCodeTelemetryPreview,
  consentToStableDict,
  createAssessInvokedEvent,
  createIsolationSession,
  defaultConsent,
  defaultUnavailableTransport,
  defaultVsCodeTelemetryRuntimePolicy,
  denyForSession,
  describeEngineCatalogMapping,
  diagnosticsToStableDict,
  evaluatePromptEligibility,
  isEligibleTelemetryCommand,
  nonInteractiveDisabledConsent,
  policyToStableDict,
  previewToStableJson,
  projectRuntimeEvent,
  runCommandWithTelemetryIsolation,
  runTelemetryConsentPrompt,
  vscodeEventTypesSubsetOfEngineCatalog,
  TelemetryProjectionError,
} from "../telemetry";

describe("vscode telemetry runtime policy", () => {
  it("is disabled by default with unavailable transport", () => {
    const policy = defaultVsCodeTelemetryRuntimePolicy();
    assert.equal(policy.policyToken, COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_URN);
    assert.equal(policy.disabledByDefault, true);
    assert.equal(policy.unavailableTransport, true);
    assert.equal(policy.localPreferencePersistence, true);
    assert.equal(policy.noInstallationIdentity, true);
    const dict = policyToStableDict(policy);
    assert.deepEqual(Object.keys(dict), [...Object.keys(dict)].sort());
    assert.ok(!JSON.stringify(dict).includes("/Users/"));
    assert.ok(!("installation_id" in dict));
    assert.ok(!("workspaceUri" in dict));
    assert.equal(dict.noInstallationIdentity, true);
  });
});

describe("vscode telemetry consent", () => {
  it("defaults remain non-persisted until an explicit preference", () => {
    for (const consent of [
      defaultConsent(),
      allowForSession(),
      denyForSession(),
      nonInteractiveDisabledConsent(),
    ]) {
      assert.equal(consent.persisted, false);
      assert.equal(consent.priorConsentReused, false);
      assert.equal(consent.scope, "command");
      const blob = JSON.stringify(consentToStableDict(consent));
      assert.ok(!("installation_id" in consentToStableDict(consent)));
      assert.ok(!blob.includes("workspaceUri"));
      assert.ok(!blob.includes("/Users/"));
    }
  });
});

describe("vscode telemetry prompt policy", () => {
  it("allows only assess commands", () => {
    assert.equal(isEligibleTelemetryCommand("codestrata.assess"), true);
    assert.equal(isEligibleTelemetryCommand("codestrata.assessWithAi"), true);
    assert.equal(isEligibleTelemetryCommand("codestrata.installEngine"), false);
    assert.equal(isEligibleTelemetryCommand("activation"), false);
    assert.equal(
      evaluatePromptEligibility({
        commandId: "codestrata.assess",
        interactive: false,
      }).reason,
      "non_interactive"
    );
  });

  it("defaults to deny on dismiss and prompt failure", async () => {
    const store: Record<string, string> = {};
    const preferenceStore = {
      get: (key: string) => store[key],
      update: async (key: string, value: string) => {
        store[key] = value;
      },
    };
    // Without Engine client, prompt path is fail-closed (Slice 20.10).
    const dismissed = await runTelemetryConsentPrompt({
      commandId: "codestrata.assess",
      interactive: true,
      preferenceStore,
      ui: {
        async showConsentPrompt() {
          return undefined;
        },
      },
    });
    assert.equal(dismissed.consent.decision, "denied_for_session");
    assert.equal(dismissed.reason, "prompt_failure");

    const failed = await runTelemetryConsentPrompt({
      commandId: "codestrata.assess",
      interactive: true,
      ui: {
        async showConsentPrompt() {
          throw new Error("ui boom");
        },
      },
    });
    assert.equal(failed.consent.decision, "denied_for_session");
    assert.equal(failed.reason, "prompt_failure");

    const suppressed = await runTelemetryConsentPrompt({
      commandId: "codestrata.assess",
      interactive: false,
    });
    assert.equal(suppressed.consent.decision, "non_interactive_disabled");
    assert.equal(suppressed.prompted, false);
  });

  it("does not treat globalState as Engine authority without client", async () => {
    const store: Record<string, string> = {
      "codestrata.telemetryPreference": "enabled",
    };
    const preferenceStore = {
      get: (key: string) => store[key],
      update: async (key: string, value: string) => {
        store[key] = value;
      },
    };
    const result = await runTelemetryConsentPrompt({
      commandId: "codestrata.assess",
      interactive: true,
      preferenceStore,
      ui: {
        async showConsentPrompt() {
          return "Allow";
        },
      },
    });
    assert.equal(result.consent.transmissionAuthorized, false);
    assert.equal(result.reason, "prompt_failure");
  });
});

describe("vscode telemetry projection", () => {
  it("projects approved fields only", () => {
    const projected = projectRuntimeEvent(
      createAssessInvokedEvent({ aiUsed: true, extensionVersion: "0.2.0" })
    );
    assert.equal(projected.fields.client_name, VSCODE_CLIENT_NAME);
    assert.equal(projected.fields.event_type, "feature_invoked");
    assert.equal(projected.fields.ai_used, true);
    assert.ok(!("workspace" in projected.fields));
    assert.ok(!("repository" in projected.fields));
    assert.ok(!("path" in projected.fields));
    assert.ok(!("installation_id" in projected.fields));
  });

  it("rejects unsafe extension versions", () => {
    assert.throws(
      () =>
        projectRuntimeEvent(
          createAssessInvokedEvent({
            aiUsed: false,
            extensionVersion: "/tmp/evil",
          })
        ),
      (err: unknown) =>
        err instanceof TelemetryProjectionError && err.code === "unsafe_value"
    );
  });
});

describe("vscode telemetry transport", () => {
  it("defaults to unavailable and never claims sent", () => {
    const transport = defaultUnavailableTransport();
    const projected = projectRuntimeEvent(
      createAssessInvokedEvent({ aiUsed: false, extensionVersion: "0.2.0" })
    );
    const result = transport.send(projected);
    assert.equal(result.kind, "unavailable");
    assert.equal(transport.transportCategory, "unavailable");
  });
});

describe("vscode telemetry isolation", () => {
  it("preserves primary success when transport raises", async () => {
    const capture = new CaptureExtensionTelemetryTransport("sent", true);
    const session = createIsolationSession({
      consent: allowForSession(),
      transport: capture,
    });
    const value = await runCommandWithTelemetryIsolation({
      session,
      aiUsed: false,
      primary: async () => "ok",
    });
    assert.equal(value, "ok");
    assert.ok(session.diagnostics.failures >= 1);
  });

  it("preserves primary failure when telemetry succeeds", async () => {
    const capture = new CaptureExtensionTelemetryTransport();
    const session = createIsolationSession({
      consent: allowForSession(),
      transport: capture,
    });
    await assert.rejects(
      () =>
        runCommandWithTelemetryIsolation({
          session,
          aiUsed: true,
          primary: async () => {
            throw new Error("command_boom");
          },
        }),
      /command_boom/
    );
    assert.ok(capture.captured.length >= 1);
  });

  it("drops events when consent denies transmission", async () => {
    const capture = new CaptureExtensionTelemetryTransport();
    const session = createIsolationSession({
      consent: denyForSession(),
      transport: capture,
    });
    await runCommandWithTelemetryIsolation({
      session,
      aiUsed: false,
      primary: async () => "done",
    });
    assert.equal(capture.captured.length, 0);
    assert.ok(session.diagnostics.eventsDropped >= 1);
  });
});

describe("vscode telemetry preview", () => {
  it("is local-only and deterministic", () => {
    const a = buildVsCodeTelemetryPreview({ extensionVersion: "0.2.0" });
    const b = buildVsCodeTelemetryPreview({ extensionVersion: "0.2.0" });
    assert.equal(a.transmissionPerformed, false);
    assert.equal(a.localOnly, true);
    assert.equal(previewToStableJson(a), previewToStableJson(b));
    const blob = previewToStableJson(a);
    assert.ok(!blob.includes("workspace"));
    assert.ok(!blob.includes("Authorization"));
  });
});

describe("vscode telemetry diagnostics", () => {
  it("excludes forbidden keys", () => {
    const session = createIsolationSession({ consent: defaultConsent() });
    const blob = JSON.stringify(diagnosticsToStableDict(session.diagnostics));
    for (const needle of [
      "workspace",
      "repository",
      "document",
      "installation",
      "machineId",
      "/Users/",
    ]) {
      assert.ok(!blob.includes(needle));
    }
  });
});

describe("vscode telemetry catalog mapping", () => {
  it("maps conceptually to Engine event vocabulary", () => {
    assert.equal(vscodeEventTypesSubsetOfEngineCatalog(), true);
    const note = describeEngineCatalogMapping();
    assert.equal(note.engineClientName, "codestrata_cli");
    assert.equal(note.vscodeClientName, "vscode_extension");
    assert.ok(note.sharedEventTypes.includes("feature_invoked"));
  });

  it("reconciles against committed Engine catalog when present", () => {
    const catalogPath = path.resolve(
      __dirname,
      "../../../engine/docs/telemetry-event-catalog.json"
    );
    if (!fs.existsSync(catalogPath)) {
      return;
    }
    const catalog = JSON.parse(fs.readFileSync(catalogPath, "utf8")) as {
      events: Array<{ name: string }>;
      client_name: string;
    };
    assert.equal(catalog.client_name, "codestrata_cli");
    const names = new Set(catalog.events.map((item) => item.name));
    for (const eventType of ["feature_invoked", "feature_completed", "operation_failed"]) {
      assert.ok(names.has(eventType), `missing ${eventType}`);
    }
  });
});

describe("vscode telemetry package boundary", () => {
  it("does not import Platform or Data Lake", () => {
    const root = path.resolve(__dirname, "../telemetry");
    const files: string[] = [];
    const walk = (dir: string) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          walk(full);
          continue;
        }
        if (entry.name.endsWith(".ts")) {
          files.push(full);
        }
      }
    };
    walk(root);
    for (const file of files) {
      const text = fs.readFileSync(file, "utf8");
      assert.ok(!text.includes("codestrata_platform"));
      assert.ok(!text.includes("boto3"));
      assert.ok(!text.includes("@aws-sdk"));
      assert.ok(!/from ["']cursor-plugin/.test(text));
    }
  });
});
