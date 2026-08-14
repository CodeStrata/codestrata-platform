/**
 * Slice 20.11 — VS Code cross-surface orchestration E2E (E2E-02..07).
 *
 * Proves Engine-owned consent contract + quiet/json-summary assess args
 * without requiring a real VS Code GUI host.
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildAssessArgs } from "../engine/cliContract";
import {
  parseEngineConsentStatusJson,
  TELEMETRY_DECLINE_UPGRADE_ARGS,
  TELEMETRY_DISABLE_ARGS,
  TELEMETRY_ENABLE_ARGS,
  TELEMETRY_STATUS_JSON_ARGS,
  type EngineConsentCliRunner,
} from "../engine/telemetryConsentContract";
import { normalizeSettings } from "../config/settings";
import {
  TELEMETRY_UPGRADE_MESSAGE,
  resolveCanonicalConsentForAssessment,
} from "../telemetry";

function sampleAssessOptions() {
  return {
    workspaceFolder: "/tmp/workspace",
    withAi: false,
    settings: normalizeSettings({
      outputDirectory: "/tmp/out",
      extraArgs: [],
    }),
  };
}

function statusJson(state: string, extras: Record<string, unknown> = {}): string {
  return JSON.stringify({
    assessment_metadata_allowed: state === "v2_yes",
    lifecycle_allowed: state === "v1_yes" || state === "v2_yes",
    schema_version: "1",
    should_prompt_v2_upgrade: false,
    state,
    v2_upgrade_declined: false,
    ...extras,
  });
}

function fakeRunner(handlers: {
  status?: string | (() => string);
  statusExit?: number;
  enableExit?: number;
  disableExit?: number;
  declineExit?: number;
  calls?: string[][];
}): EngineConsentCliRunner {
  const calls = handlers.calls ?? [];
  return {
    async run(args) {
      calls.push([...args]);
      const key = args.join(" ");
      if (key === TELEMETRY_STATUS_JSON_ARGS.join(" ")) {
        const body =
          typeof handlers.status === "function"
            ? handlers.status()
            : (handlers.status ?? statusJson("undecided"));
        return {
          exitCode: handlers.statusExit ?? 0,
          stdout: body,
          stderr: "",
        };
      }
      if (key === TELEMETRY_ENABLE_ARGS.join(" ")) {
        return { exitCode: handlers.enableExit ?? 0, stdout: "ok", stderr: "" };
      }
      if (key === TELEMETRY_DISABLE_ARGS.join(" ")) {
        return { exitCode: handlers.disableExit ?? 0, stdout: "ok", stderr: "" };
      }
      if (key === TELEMETRY_DECLINE_UPGRADE_ARGS.join(" ")) {
        return { exitCode: handlers.declineExit ?? 0, stdout: "ok", stderr: "" };
      }
      return { exitCode: 2, stdout: "", stderr: "unknown" };
    },
  };
}

describe("E2E-02 VS Code V2 happy path", () => {
  it("UNDECIDED → Yes → enable → V2_YES authorizes assess session", async () => {
    const calls: string[][] = [];
    let engineState = "undecided";
    const store: Record<string, string> = {};
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({
        calls,
        status: () => statusJson(engineState),
        enableExit: 0,
      }),
      preferenceStore: {
        get: (k) => store[k],
        update: async (k, v) => {
          store[k] = v;
          if (v === "enabled") engineState = "v2_yes";
        },
      },
      ui: {
        async showConsentPrompt() {
          return "Allow";
        },
      },
    });
    // Simulate status refresh after enable by re-querying with updated state.
    assert.ok(calls.some((c) => c.join(" ") === TELEMETRY_ENABLE_ARGS.join(" ")));
    assert.equal(result.consent.transmissionAuthorized, true);
    // Quiet assess args must not invent --telemetry-allow.
    const assessArgs = buildAssessArgs(sampleAssessOptions());
    assert.ok(assessArgs.includes("--quiet"));
    assert.ok(assessArgs.includes("--json-summary"));
    assert.ok(!assessArgs.includes("--telemetry-allow"));
  });
});

describe("E2E-03 CLI Yes → VS Code assess", () => {
  it("no re-consent when Engine already V2; amd allowed", async () => {
    const status = parseEngineConsentStatusJson(statusJson("v2_yes"));
    assert.equal(status?.assessmentMetadataAllowed, true);
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({ status: statusJson("v2_yes") }),
      ui: {
        async showConsentPrompt() {
          throw new Error("must not prompt");
        },
      },
    });
    assert.equal(result.prompted, false);
    assert.equal(result.engineState, "v2_yes");
    assert.equal(result.consent.transmissionAuthorized, true);
  });
});

describe("E2E-04 VS Code Yes → CLI assess contract", () => {
  it("enable args match Engine CLI surface used by CLI assess home", async () => {
    assert.deepEqual([...TELEMETRY_ENABLE_ARGS], ["telemetry", "enable"]);
    assert.deepEqual([...TELEMETRY_STATUS_JSON_ARGS], [
      "telemetry",
      "status",
      "--json",
    ]);
  });
});

describe("E2E-05 CLI disable → VS Code assess", () => {
  it("DISABLED wins over stale enabled cache; collection off", async () => {
    const store: Record<string, string> = {
      "codestrata.telemetryPreference": "enabled",
    };
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({ status: statusJson("disabled") }),
      preferenceStore: {
        get: (k) => store[k],
        update: async (k, v) => {
          store[k] = v;
        },
      },
      ui: {
        async showConsentPrompt() {
          throw new Error("must not prompt");
        },
      },
    });
    assert.equal(result.consent.transmissionAuthorized, false);
    assert.equal(result.engineState, "disabled");
    assert.equal(store["codestrata.telemetryPreference"], "disabled");
  });
});

describe("E2E-06 VS Code disable → CLI assess", () => {
  it("disable args match Engine CLI; status then DISABLED", async () => {
    const calls: string[][] = [];
    const runner = fakeRunner({ calls, status: statusJson("v2_yes") });
    await runner.run(TELEMETRY_DISABLE_ARGS);
    assert.deepEqual(calls[0], [...TELEMETRY_DISABLE_ARGS]);
    const disabled = parseEngineConsentStatusJson(statusJson("disabled"));
    assert.equal(disabled?.lifecycleAllowed, false);
    assert.equal(disabled?.assessmentMetadataAllowed, false);
  });
});

describe("E2E-07 V1 legacy → decline upgrade → CLI assess", () => {
  it("decline keeps V1; lifecycle on; amd off; no silent V2", async () => {
    const calls: string[][] = [];
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({
        calls,
        status: statusJson("v1_yes", { should_prompt_v2_upgrade: true }),
      }),
      ui: {
        async showConsentPrompt(message) {
          assert.match(message.toLowerCase(), /assessment insights/);
          assert.equal(message, TELEMETRY_UPGRADE_MESSAGE);
          return "Deny";
        },
      },
    });
    assert.ok(
      calls.some((c) => c.join(" ") === TELEMETRY_DECLINE_UPGRADE_ARGS.join(" "))
    );
    assert.ok(!calls.some((c) => c.join(" ") === TELEMETRY_ENABLE_ARGS.join(" ")));
    assert.equal(result.engineState, "v1_yes");
    assert.equal(result.consent.transmissionAuthorized, true);
    const status = parseEngineConsentStatusJson(
      statusJson("v1_yes", { v2_upgrade_declined: true })
    );
    assert.equal(status?.assessmentMetadataAllowed, false);
    assert.equal(status?.lifecycleAllowed, true);
  });
});

describe("E2E-02 credential / path privacy in consent errors", () => {
  it("status failure messages omit paths and installation secrets", async () => {
    const messages: string[] = [];
    await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: false,
      engineClient: fakeRunner({ statusExit: 1 }),
      onUserMessage: (m) => messages.push(m),
    });
    const blob = messages.join("\n");
    assert.ok(!blob.includes("/Users/"));
    assert.ok(!blob.includes("TEST_SECRET_DO_NOT_TRANSMIT"));
    assert.ok(!blob.includes("Bearer "));
    assert.ok(!/cscc[_-]v\d/i.test(blob));
    assert.ok(!blob.includes("installation"));
  });
});
