/**
 * Slice 13.2 CLI discovery unit tests (injected runner; no live CLI required).
 */

import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { describe, it } from "node:test";

import {
  CANDIDATE_SOURCE_PRECEDENCE,
  CLI_DISCOVERY_POLICY_ID,
  CLI_DISCOVERY_POLICY_VERSION,
  VERSION_PROBE_ARGS,
  classifyDiscoveryCompatibility,
  cliDiscoveryPolicyToStableDict,
  cliDiscoveryResultToStableDict,
  createCliDiscoveryPolicy,
  discoverCodeStrataCli,
  discoveryDiagnosticsContainForbiddenKeys,
  discoveryDiagnosticsToStableDict,
  discoveryDiagnosticsFromResult,
  listDiscoveryCandidates,
  parseProductIdentityOutput,
  parseSemanticVersion,
  validateExplicitExecutable,
  type ProbeRunRequest,
  type ProbeRunner,
} from "../cliDiscovery";
import { CommunityWorkflowSession } from "../communityWorkflow";

function mockRunner(handlers: {
  readonly byExecutable?: Record<string, { stdout: string; exitCode?: number }>;
  readonly defaultResponse?: {
    stdout: string;
    exitCode?: number;
    timedOut?: boolean;
    outputExceeded?: boolean;
    spawnErrorCode?: string;
  };
  readonly onCall?: (req: ProbeRunRequest) => void;
}): ProbeRunner {
  return async (request) => {
    handlers.onCall?.(request);
    assert.deepEqual([...request.args], [...VERSION_PROBE_ARGS]);
    assert.equal(request.env?.CI, "1");
    const mapped = handlers.byExecutable?.[request.executable];
    if (mapped) {
      return {
        exitCode: mapped.exitCode ?? 0,
        stdout: mapped.stdout,
        stderr: "",
        timedOut: false,
        outputExceeded: false,
      };
    }
    const fallback = handlers.defaultResponse ?? {
      stdout: "",
      exitCode: 1,
      spawnErrorCode: "ENOENT",
    };
    return {
      exitCode: fallback.exitCode ?? 1,
      stdout: fallback.stdout ?? "",
      stderr: "",
      timedOut: fallback.timedOut ?? false,
      outputExceeded: fallback.outputExceeded ?? false,
      spawnErrorCode: fallback.spawnErrorCode,
    };
  };
}

describe("cli discovery policy", () => {
  it("serializes deterministically without paths or timestamps", () => {
    const a = cliDiscoveryPolicyToStableDict(createCliDiscoveryPolicy());
    const b = cliDiscoveryPolicyToStableDict(createCliDiscoveryPolicy());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, CLI_DISCOVERY_POLICY_ID);
    assert.equal(a.policy_version, CLI_DISCOVERY_POLICY_VERSION);
    assert.equal(a.local_only, true);
    assert.equal(a.network_allowed, false);
    assert.equal(a.installation_allowed, false);
    assert.equal(a.invalid_explicit_fails_closed, true);
    assert.equal(JSON.stringify(a).includes("timestamp"), false);
    assert.equal(JSON.stringify(a).includes("/Users/"), false);
  });
});

describe("semantic version parser", () => {
  it("parses strict semver and rejects malformed values", () => {
    assert.deepEqual(parseSemanticVersion("0.2.0"), {
      major: 0,
      minor: 2,
      patch: 0,
    });
    assert.equal(parseSemanticVersion("1.0"), undefined);
    assert.equal(parseSemanticVersion("0.2.0\u0000"), undefined);
    assert.equal(parseSemanticVersion("v0.2.0"), undefined);
  });
});

describe("product identity", () => {
  it("requires CodeStrata identity and rejects bare semver", () => {
    const ok = parseProductIdentityOutput("CodeStrata 0.2.0\nCLI: 0.2.0\n");
    assert.equal(ok.ok, true);
    if (ok.ok) {
      assert.equal(ok.version.major, 0);
    }
    assert.equal(parseProductIdentityOutput("0.2.0").ok, false);
    assert.equal(
      parseProductIdentityOutput("codestrata-compatible 0.2.0").ok,
      false
    );
    assert.equal(
      parseProductIdentityOutput("CodeStrata 0.2.0\nCodeStrata 0.3.0").ok,
      false
    );
  });
});

describe("compatibility decision", () => {
  it("accepts CLI 0.2.x and rejects 0.1.x / 1.x / prerelease", () => {
    assert.equal(
      classifyDiscoveryCompatibility({ major: 0, minor: 2, patch: 0 }),
      "compatible"
    );
    assert.equal(
      classifyDiscoveryCompatibility({ major: 0, minor: 2, patch: 9 }),
      "compatible"
    );
    assert.equal(
      classifyDiscoveryCompatibility({ major: 1, minor: 0, patch: 0 }),
      "incompatible_major"
    );
    assert.equal(
      classifyDiscoveryCompatibility({ major: 0, minor: 1, patch: 0 }),
      "incompatible_below_minimum"
    );
    assert.equal(
      classifyDiscoveryCompatibility({ major: 0, minor: 3, patch: 0 }),
      "incompatible_above_supported"
    );
    assert.equal(
      classifyDiscoveryCompatibility({
        major: 0,
        minor: 2,
        patch: 0,
        prerelease: "rc.1",
      }),
      "incompatible_prerelease"
    );
  });
});

describe("candidate sources and precedence", () => {
  it("uses explicit configuration alone when non-default", () => {
    const candidates = listDiscoveryCandidates({
      configuredExecutable: "/opt/codestrata",
      workspaceFolders: [],
      env: {},
      platform: "linux",
    });
    assert.equal(candidates.length, 1);
    assert.equal(candidates[0].source, "explicit_configuration");
    assert.deepEqual(CANDIDATE_SOURCE_PRECEDENCE[0], "explicit_configuration");
  });

  it("falls back to PATH name for default setting", () => {
    const candidates = listDiscoveryCandidates({
      configuredExecutable: "codestrata",
      workspaceFolders: [],
      env: {},
      platform: "linux",
    });
    assert.equal(candidates.some((c) => c.source === "process_path"), true);
    assert.equal(
      candidates.some((c) => c.source === "explicit_configuration"),
      false
    );
  });
});

describe("executable validation", () => {
  it("rejects directories and missing files", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "cs-cli-"));
    try {
      assert.equal(validateExplicitExecutable(dir).status, "not_file");
      assert.equal(
        validateExplicitExecutable(path.join(dir, "missing")).status,
        "missing"
      );
      assert.equal(
        validateExplicitExecutable("$(evil)").status,
        "unsupported"
      );
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });

  it("accepts an executable file on POSIX", () => {
    if (process.platform === "win32") {
      return;
    }
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "cs-cli-"));
    const file = path.join(dir, "codestrata");
    try {
      fs.writeFileSync(file, "#!/bin/sh\necho ok\n", { mode: 0o755 });
      assert.equal(validateExplicitExecutable(file).status, "ok");
      fs.chmodSync(file, 0o644);
      assert.equal(validateExplicitExecutable(file).status, "not_executable");
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });
});

describe("discoverCodeStrataCli", () => {
  it("fail-closed: invalid explicit path does not fall back to PATH", async () => {
    let calls = 0;
    const outcome = await discoverCodeStrataCli({
      configuredExecutable: "/tmp/this-codestrata-does-not-exist-13-2",
      workspaceFolders: [],
      env: {},
      platform: "linux",
      runner: mockRunner({
        onCall: () => {
          calls += 1;
        },
        defaultResponse: {
          stdout: "CodeStrata 0.2.0\n",
          exitCode: 0,
        },
      }),
    });
    assert.equal(outcome.public.status, "not_found");
    assert.equal(outcome.public.candidate_source, "explicit_configuration");
    assert.equal(outcome.resolved, undefined);
    assert.equal(calls, 0);
  });

  it("accepts PATH candidate with valid identity", async () => {
    const outcome = await discoverCodeStrataCli({
      configuredExecutable: "codestrata",
      workspaceFolders: [],
      env: {},
      platform: "linux",
      runner: mockRunner({
        byExecutable: {
          codestrata: { stdout: "CodeStrata 0.2.0\nCLI: 0.2.0\n" },
        },
      }),
    });
    assert.equal(outcome.public.status, "compatible");
    assert.equal(outcome.public.candidate_source, "process_path");
    assert.equal(outcome.resolved?.version, "0.2.0");
    assert.equal(outcome.resolved?.command, "codestrata");
  });

  it("rejects non-CodeStrata identity on PATH", async () => {
    const outcome = await discoverCodeStrataCli({
      configuredExecutable: "codestrata",
      workspaceFolders: [],
      env: {},
      platform: "linux",
      runner: mockRunner({
        byExecutable: {
          codestrata: { stdout: "0.2.0\n" },
        },
      }),
    });
    assert.equal(outcome.public.status, "identity_mismatch");
    assert.equal(outcome.resolved, undefined);
  });

  it("rejects CLI 1.x for extension 0.2.0", async () => {
    const outcome = await discoverCodeStrataCli({
      configuredExecutable: "codestrata",
      workspaceFolders: [],
      env: {},
      platform: "linux",
      runner: mockRunner({
        byExecutable: {
          codestrata: { stdout: "CodeStrata 1.0.0\n" },
        },
      }),
    });
    assert.equal(outcome.public.status, "incompatible");
    assert.equal(outcome.public.compatibility_category, "incompatible_major");
  });

  it("handles probe timeout and does not expose stdout in public result", async () => {
    const outcome = await discoverCodeStrataCli({
      configuredExecutable: "codestrata",
      workspaceFolders: [],
      env: {},
      platform: "linux",
      runner: mockRunner({
        defaultResponse: {
          stdout: "secret-path-/Users/me",
          exitCode: 1,
          timedOut: true,
        },
      }),
    });
    assert.equal(outcome.public.status, "probe_timed_out");
    const stable = cliDiscoveryResultToStableDict(outcome.public);
    assert.equal("stdout" in stable, false);
    assert.equal(JSON.stringify(stable).includes("/Users/"), false);
    assert.equal(
      discoveryDiagnosticsContainForbiddenKeys(
        discoveryDiagnosticsToStableDict(
          discoveryDiagnosticsFromResult(outcome.public)
        )
      ).length,
      0
    );
  });

  it("never uses assess/init probe args", async () => {
    const seen: string[][] = [];
    await discoverCodeStrataCli({
      configuredExecutable: "codestrata",
      workspaceFolders: [],
      env: {},
      platform: "linux",
      runner: mockRunner({
        onCall: (req) => seen.push([...req.args]),
        byExecutable: {
          codestrata: { stdout: "CodeStrata 0.2.0\n" },
        },
      }),
    });
    assert.deepEqual(seen, [["version"]]);
  });
});

describe("workflow discovery integration counts", () => {
  it("keeps product CLI invocation separate from discovery probes", () => {
    const session = new CommunityWorkflowSession({
      operation: "run_assessment",
    });
    session.transitionTo("validating_workspace");
    session.recordDiscoveryProbe();
    session.recordDiscoveryProbe();
    session.setDiscoveryStatus("compatible");
    session.transitionTo("awaiting_consent");
    session.transitionTo("running_assessment");
    session.recordCliInvocation();
    session.complete({
      status: "success",
      primaryExit: "success",
    });
    assert.equal(session.getDiscoveryProbeCount(), 2);
    assert.equal(session.getCliInvocationCount(), 1);
    assert.equal(session.getDiscoveryStatus(), "compatible");
    const diag = session.diagnosticsStable();
    assert.equal(diag.discovery_probe_count, 2);
    assert.equal(diag.cli_invocation_count, 1);
    assert.equal("cli_path" in diag, false);
  });
});
