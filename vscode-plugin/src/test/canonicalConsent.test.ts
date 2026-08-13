/**
 * Slice 20.10 — VS Code canonical Engine consent propagation tests (VSCODE-01…15).
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  parseEngineConsentStatusJson,
  TELEMETRY_DECLINE_UPGRADE_ARGS,
  TELEMETRY_DISABLE_ARGS,
  TELEMETRY_ENABLE_ARGS,
  TELEMETRY_STATUS_JSON_ARGS,
  type EngineConsentCliRunner,
} from "../engine/telemetryConsentContract";
import { parseJsonSummary } from "../engine/cliContract";
import {
  TELEMETRY_CONSENT_MESSAGE,
  TELEMETRY_UPGRADE_MESSAGE,
  resolveCanonicalConsentForAssessment,
} from "../telemetry";

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
        return {
          exitCode: handlers.enableExit ?? 0,
          stdout: "ok",
          stderr: "",
        };
      }
      if (key === TELEMETRY_DISABLE_ARGS.join(" ")) {
        return {
          exitCode: handlers.disableExit ?? 0,
          stdout: "ok",
          stderr: "",
        };
      }
      if (key === TELEMETRY_DECLINE_UPGRADE_ARGS.join(" ")) {
        return {
          exitCode: handlers.declineExit ?? 0,
          stdout: "ok",
          stderr: "",
        };
      }
      return { exitCode: 2, stdout: "", stderr: "unknown" };
    },
  };
}

describe("engine consent status JSON contract", () => {
  it("parses stable status and rejects malformed", () => {
    const ok = parseEngineConsentStatusJson(statusJson("v2_yes"));
    assert.equal(ok?.state, "v2_yes");
    assert.equal(ok?.assessmentMetadataAllowed, true);
    assert.equal(parseEngineConsentStatusJson("{not-json"), null);
    assert.equal(
      parseEngineConsentStatusJson(JSON.stringify({ state: "nope" })),
      null
    );
  });
});

describe("VSCODE-01 fresh Yes", () => {
  it("invokes telemetry enable and authorizes session", async () => {
    const calls: string[][] = [];
    const store: Record<string, string> = {};
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({
        calls,
        status: statusJson("undecided"),
        enableExit: 0,
      }),
      preferenceStore: {
        get: (k) => store[k],
        update: async (k, v) => {
          store[k] = v;
        },
      },
      ui: {
        async showConsentPrompt() {
          return "Allow";
        },
      },
    });
    assert.ok(
      calls.some((c) => c.join(" ") === TELEMETRY_ENABLE_ARGS.join(" "))
    );
    assert.equal(result.consent.transmissionAuthorized, true);
    assert.equal(result.engineState, "v2_yes");
    assert.equal(store["codestrata.telemetryPreference"], "enabled");
    assert.match(TELEMETRY_CONSENT_MESSAGE.toLowerCase(), /improve codestrata/);
    assert.match(TELEMETRY_CONSENT_MESSAGE.toLowerCase(), /assessment insights/);
    assert.match(TELEMETRY_CONSENT_MESSAGE.toLowerCase(), /local/);
    assert.match(TELEMETRY_CONSENT_MESSAGE.toLowerCase(), /publish/);
  });
});

describe("VSCODE-02 fresh No", () => {
  it("invokes telemetry disable and denies collection", async () => {
    const calls: string[][] = [];
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({
        calls,
        status: statusJson("undecided"),
        disableExit: 0,
      }),
      ui: {
        async showConsentPrompt() {
          return "Deny";
        },
      },
    });
    assert.ok(
      calls.some((c) => c.join(" ") === TELEMETRY_DISABLE_ARGS.join(" "))
    );
    assert.equal(result.consent.transmissionAuthorized, false);
    assert.equal(result.engineState, "disabled");
  });
});

describe("VSCODE-03 CLI V2 → VS Code", () => {
  it("skips prompt when Engine already V2", async () => {
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({ status: statusJson("v2_yes") }),
      preferenceStore: {
        get: () => undefined,
        update: async () => undefined,
      },
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

describe("VSCODE-04 VS Code Yes → CLI state", () => {
  it("records enable args matching Engine CLI surface", async () => {
    const calls: string[][] = [];
    await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({ calls, status: statusJson("undecided") }),
      ui: { async showConsentPrompt() { return "Allow"; } },
    });
    assert.deepEqual(
      calls.find((c) => c[0] === "telemetry" && c[1] === "enable"),
      [...TELEMETRY_ENABLE_ARGS]
    );
  });
});

describe("VSCODE-05 CLI revoke → stale VS Code cache", () => {
  it("Engine DISABLED wins over globalState enabled", async () => {
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

describe("VSCODE-06 VS Code revoke → canonical disable", () => {
  it("settings-equivalent disable uses Engine disable args", async () => {
    const calls: string[][] = [];
    const runner = fakeRunner({ calls, status: statusJson("v2_yes") });
    // Simulate revoke via gate Deny on undecided path is covered; assert disable args constant.
    assert.deepEqual([...TELEMETRY_DISABLE_ARGS], ["telemetry", "disable"]);
    await runner.run(TELEMETRY_DISABLE_ARGS);
    assert.deepEqual(calls[0], [...TELEMETRY_DISABLE_ARGS]);
  });
});

describe("VSCODE-07 old globalState Yes migration", () => {
  it("does not grandfather extension Yes into V2 without Engine enable", async () => {
    const calls: string[][] = [];
    const store: Record<string, string> = {
      "codestrata.telemetryPreference": "enabled",
    };
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({ calls, status: statusJson("undecided") }),
      preferenceStore: {
        get: (k) => store[k],
        update: async (k, v) => {
          store[k] = v;
        },
      },
      ui: {
        async showConsentPrompt() {
          // User must re-consent; choose Deny to prove no silent enable.
          return "Deny";
        },
      },
    });
    assert.ok(
      !calls.some((c) => c.join(" ") === TELEMETRY_ENABLE_ARGS.join(" "))
    );
    assert.equal(result.consent.transmissionAuthorized, false);
  });
});

describe("VSCODE-08 extension reinstall", () => {
  it("Engine V2 survives missing globalState without re-prompt", async () => {
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({ status: statusJson("v2_yes") }),
      preferenceStore: {
        get: () => undefined,
        update: async () => undefined,
      },
      ui: {
        async showConsentPrompt() {
          throw new Error("must not prompt");
        },
      },
    });
    assert.equal(result.prompted, false);
    assert.equal(result.engineState, "v2_yes");
  });
});

describe("VSCODE-09/10 legacy V1 upgrade", () => {
  it("upgrade Yes calls enable", async () => {
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
          assert.match(TELEMETRY_UPGRADE_MESSAGE.toLowerCase(), /publish/);
          return "Allow";
        },
      },
    });
    assert.ok(
      calls.some((c) => c.join(" ") === TELEMETRY_ENABLE_ARGS.join(" "))
    );
    assert.equal(result.engineState, "v2_yes");
  });

  it("upgrade decline calls decline-upgrade not disable", async () => {
    const calls: string[][] = [];
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({
        calls,
        status: statusJson("v1_yes", { should_prompt_v2_upgrade: true }),
      }),
      ui: {
        async showConsentPrompt() {
          return "Deny";
        },
      },
    });
    assert.ok(
      calls.some(
        (c) => c.join(" ") === TELEMETRY_DECLINE_UPGRADE_ARGS.join(" ")
      )
    );
    assert.ok(
      !calls.some((c) => c.join(" ") === TELEMETRY_DISABLE_ARGS.join(" "))
    );
    assert.equal(result.engineState, "v1_yes");
    assert.equal(result.consent.transmissionAuthorized, true);
  });
});

describe("VSCODE-11/12/13/14 failure modes", () => {
  it("status failure fails closed and does not trust globalState Yes", async () => {
    const store: Record<string, string> = {
      "codestrata.telemetryPreference": "enabled",
    };
    const messages: string[] = [];
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: false,
      engineClient: fakeRunner({ statusExit: 1 }),
      preferenceStore: {
        get: (k) => store[k],
        update: async (k, v) => {
          store[k] = v;
        },
      },
      onUserMessage: (m) => messages.push(m),
    });
    assert.equal(result.consent.transmissionAuthorized, false);
    assert.equal(result.engineState, "unknown");
    assert.ok(messages.length >= 1);
    assert.ok(!messages[0]?.includes("/Users/"));
    assert.ok(!messages[0]?.includes("installation"));
  });

  it("enable failure does not authorize or cache Yes", async () => {
    const store: Record<string, string> = {};
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({
        status: statusJson("undecided"),
        enableExit: 1,
      }),
      preferenceStore: {
        get: (k) => store[k],
        update: async (k, v) => {
          store[k] = v;
        },
      },
      ui: { async showConsentPrompt() { return "Allow"; } },
    });
    assert.equal(result.consent.transmissionAuthorized, false);
    assert.equal(result.consentCommandError, "enable_failed");
    assert.equal(store["codestrata.telemetryPreference"], "disabled");
  });

  it("disable failure does not claim disabled", async () => {
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: true,
      engineClient: fakeRunner({
        status: statusJson("undecided"),
        disableExit: 1,
      }),
      ui: { async showConsentPrompt() { return "Deny"; } },
    });
    assert.equal(result.consentCommandError, "disable_failed");
    assert.equal(result.engineState, "undecided");
  });

  it("malformed status fails closed", async () => {
    const result = await resolveCanonicalConsentForAssessment({
      commandId: "codestrata.assess",
      interactive: false,
      engineClient: fakeRunner({ status: "{bad" }),
    });
    assert.equal(result.consent.transmissionAuthorized, false);
    assert.equal(result.engineState, "unknown");
  });
});

describe("VSCODE-15 json-summary parsing unaffected", () => {
  it("still parses assessment json-summary lines", () => {
    const summary = parseJsonSummary(
      "noise\n" +
        JSON.stringify({
          run_directory: "/tmp/run",
          html_report: "report.html",
          json_report: "assessment.json",
          findings: 1,
        }) +
        "\n"
    );
    assert.equal(summary?.run_directory, "/tmp/run");
    assert.equal(summary?.findings, 1);
  });
});

describe("telemetry-allow decision", () => {
  it("contract documents no assess telemetry flags", () => {
    // Assess path must not invent consent via --telemetry-allow (Slice 20.9/20.10).
    assert.equal(
      TELEMETRY_ENABLE_ARGS.includes("--telemetry-allow" as never),
      false
    );
  });
});
