/**
 * Slice 13.3 CLI installation guidance unit tests (Approach A).
 */

import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  automaticInstallationAllowed,
  cliInstallationPolicyToStableDict,
  createCliInstallationPolicy,
  CLI_INSTALLATION_POLICY_ID,
  CLI_INSTALLATION_POLICY_VERSION,
  guidanceNotRequired,
  installationDiagnosticsContainForbiddenKeys,
  installationDiagnosticsToStableDict,
  installationGuidanceResultToStableDict,
  installationMethodCatalog,
  mapDiscoveryToGuidanceCategory,
  methodCatalogToStableDict,
  runInstallationGuidance,
  trustedCommandForMethod,
  TRUSTED_COMMAND_TEMPLATES,
  type InstallationUiAdapters,
} from "../cliInstallation";
import { installEngine } from "../engine/installer";

function mockAdapters(
  overrides: Partial<InstallationUiAdapters> & {
    readonly actions?: string[];
    readonly pick?: string;
  } = {}
): InstallationUiAdapters & { calls: string[] } {
  const calls: string[] = [];
  const actions = [...(overrides.actions ?? ["Cancel"])];
  return {
    calls,
    async showActions(message, _actions) {
      calls.push(`showActions:${message.slice(0, 24)}`);
      return actions.shift();
    },
    async showQuickPick(_items, _title) {
      calls.push("showQuickPick");
      return overrides.pick;
    },
    async copyText(text) {
      calls.push(`copy:${text}`);
      return overrides.copyText ? overrides.copyText(text) : true;
    },
    async openTerminal() {
      calls.push("openTerminal");
      return overrides.openTerminal ? overrides.openTerminal() : true;
    },
    async openExternalUrl(url) {
      calls.push(`openUrl:${url.startsWith("https://")}`);
      return overrides.openExternalUrl
        ? overrides.openExternalUrl(url)
        : true;
    },
    async openExecutableSettings() {
      calls.push("openSettings");
      await overrides.openExecutableSettings?.();
    },
    async refreshDiscovery() {
      calls.push("refresh");
      return overrides.refreshDiscovery
        ? overrides.refreshDiscovery()
        : "not_found";
    },
    appendOutputLine(line) {
      calls.push(`out:${line.slice(0, 40)}`);
      overrides.appendOutputLine?.(line);
    },
  };
}

describe("cli installation policy", () => {
  it("serializes deterministically as guidance-only", () => {
    const a = cliInstallationPolicyToStableDict(createCliInstallationPolicy());
    const b = cliInstallationPolicyToStableDict(createCliInstallationPolicy());
    assert.equal(JSON.stringify(a), JSON.stringify(b));
    assert.equal(a.policy_id, CLI_INSTALLATION_POLICY_ID);
    assert.equal(a.policy_version, CLI_INSTALLATION_POLICY_VERSION);
    assert.equal(a.approach, "guidance_only");
    assert.equal(a.automatic_installation_allowed, false);
    assert.equal(a.path_mutation_allowed, false);
    assert.equal(a.persistence_allowed, false);
    assert.equal(JSON.stringify(a).includes("timestamp"), false);
    assert.equal(JSON.stringify(a).includes("/Users/"), false);
  });
});

describe("method catalog", () => {
  it("exposes fixed trusted templates without auto-execution", () => {
    const catalog = installationMethodCatalog();
    assert.ok(catalog.every((m) => m.automatic_execution_allowed === false));
    assert.equal(
      trustedCommandForMethod("python_package", "linux"),
      TRUSTED_COMMAND_TEMPLATES.python_package_posix
    );
    assert.equal(
      trustedCommandForMethod("python_package", "windows"),
      TRUSTED_COMMAND_TEMPLATES.python_package_windows
    );
    const stable = methodCatalogToStableDict();
    assert.equal(JSON.stringify(stable).includes("sudo"), false);
    assert.equal(JSON.stringify(stable).includes("curl"), false);
  });
});

describe("discovery mapping", () => {
  it("maps discovery statuses to guidance categories", () => {
    assert.equal(mapDiscoveryToGuidanceCategory("compatible"), "none");
    assert.equal(mapDiscoveryToGuidanceCategory("not_found"), "install_cli");
    assert.equal(
      mapDiscoveryToGuidanceCategory("invalid_configuration"),
      "correct_cli_setting"
    );
    assert.equal(
      mapDiscoveryToGuidanceCategory("identity_mismatch"),
      "replace_non_codestrata_executable"
    );
    assert.equal(
      mapDiscoveryToGuidanceCategory("incompatible"),
      "install_supported_version"
    );
    assert.equal(guidanceNotRequired().status, "not_required");
  });
});

describe("runInstallationGuidance", () => {
  it("returns not_required for compatible CLI without UI mutation", async () => {
    const adapters = mockAdapters();
    const result = await runInstallationGuidance({
      discoveryStatus: "compatible",
      platform: "linux",
      adapters,
    });
    assert.equal(result.status, "not_required");
    assert.equal(adapters.calls.some((c) => c.startsWith("copy:")), false);
    assert.equal(adapters.calls.includes("openTerminal"), false);
  });

  it("copies a trusted command only after explicit user choice", async () => {
    const adapters = mockAdapters({
      actions: ["Show Installation Options"],
      pick: "python_package",
    });
    const result = await runInstallationGuidance({
      discoveryStatus: "not_found",
      platform: "linux",
      adapters,
    });
    assert.equal(result.status, "command_copied");
    assert.ok(
      adapters.calls.some((c) =>
        c.includes(TRUSTED_COMMAND_TEMPLATES.python_package_posix)
      )
    );
    const stable = installationGuidanceResultToStableDict(result);
    assert.equal("command" in stable, false);
    assert.equal(JSON.stringify(stable).includes("pip install"), false);
  });

  it("opens terminal without implying installation success", async () => {
    const adapters = mockAdapters({
      actions: ["Show Installation Options"],
      pick: "terminal_guidance",
    });
    const result = await runInstallationGuidance({
      discoveryStatus: "not_found",
      platform: "macos",
      adapters,
    });
    assert.equal(result.status, "terminal_opened");
    assert.equal(result.rediscovery_attempted, false);
  });

  it("refreshes discovery only on explicit action", async () => {
    const adapters = mockAdapters({
      actions: ["Refresh CLI Detection"],
      refreshDiscovery: async () => "compatible",
    });
    const result = await runInstallationGuidance({
      discoveryStatus: "not_found",
      platform: "linux",
      adapters,
    });
    assert.equal(result.status, "rediscovery_succeeded");
    assert.equal(result.rediscovery_attempted, true);
  });
});

describe("automatic installation boundary", () => {
  it("forbids automatic installation at policy and installer API", async () => {
    assert.equal(automaticInstallationAllowed(), false);
    const result = await installEngine({ preferredMethodId: "pip-user" });
    assert.equal(result.ok, false);
    assert.match(result.reason ?? "", /forbidden/i);
  });
});

describe("installation diagnostics privacy", () => {
  it("rejects command/url/path keys", () => {
    const diag = installationDiagnosticsToStableDict({
      installation_policy_version: CLI_INSTALLATION_POLICY_VERSION,
      approach: "guidance_only",
      discovery_status: "not_found",
      guidance_status: "guidance_available",
      method_category: "python_package",
      user_action_required: true,
      rediscovery_attempted: false,
      rediscovery_outcome: "not_attempted",
      guidance_category: "install_cli",
      limitation_codes: ["guidance_only_approach"],
    });
    assert.equal(installationDiagnosticsContainForbiddenKeys(diag).length, 0);
    assert.deepEqual(
      installationDiagnosticsContainForbiddenKeys({
        ...diag,
        command: "pip install",
      }),
      ["command", "sensitive_value"]
    );
  });
});
