/**
 * Installation guidance orchestrator (Slice 13.3 Approach A).
 * Explicit user actions only — never executes package managers or downloads.
 */

import type { CliDiscoveryStatus } from "../cliDiscovery/results";
import {
  installationMethodCatalog,
  trustedCommandForMethod,
  TRUSTED_INSTALLATION_DOCS_URL,
  type InstallationMethodId,
} from "./methods";
import {
  DEFAULT_INSTALLATION_LIMITATIONS,
} from "./policy";
import {
  guidanceNotRequired,
  mapDiscoveryToGuidanceCategory,
  type InstallationGuidanceResult,
  type InstallationGuidanceStatus,
} from "./results";

export type InstallationPlatform = "windows" | "macos" | "linux";

export type InstallationUiAdapters = {
  readonly showActions: (
    message: string,
    actions: readonly string[]
  ) => Promise<string | undefined>;
  readonly showQuickPick: (
    items: readonly { label: string; description?: string; id: string }[],
    title: string
  ) => Promise<string | undefined>;
  readonly copyText: (text: string) => Promise<boolean>;
  readonly openTerminal: () => Promise<boolean>;
  readonly openExternalUrl: (url: string) => Promise<boolean>;
  readonly openExecutableSettings: () => Promise<void>;
  readonly refreshDiscovery: () => Promise<CliDiscoveryStatus>;
  readonly appendOutputLine: (line: string) => void;
};

export type RunInstallationGuidanceInput = {
  readonly discoveryStatus: CliDiscoveryStatus | "not_attempted";
  readonly platform: InstallationPlatform;
  readonly adapters: InstallationUiAdapters;
  readonly limitations?: readonly string[];
};

function platformFromNode(platform: NodeJS.Platform): InstallationPlatform {
  if (platform === "win32") {
    return "windows";
  }
  if (platform === "darwin") {
    return "macos";
  }
  return "linux";
}

export function detectInstallationPlatform(
  platform: NodeJS.Platform = process.platform
): InstallationPlatform {
  return platformFromNode(platform);
}

function guidanceMessage(
  discoveryStatus: CliDiscoveryStatus | "not_attempted"
): string {
  switch (discoveryStatus) {
    case "compatible":
      return "CodeStrata Engine CLI is ready. Installation guidance is not required.";
    case "invalid_configuration":
    case "not_executable":
      return "Configured CodeStrata CLI cannot be used. Correct or clear codestrata.engine.executable, then refresh detection. The extension will not replace the setting automatically.";
    case "identity_mismatch":
      return "The selected executable is not a CodeStrata CLI. Install CodeStrata Engine or point the setting at a valid CLI.";
    case "incompatible":
      return "Detected CodeStrata CLI version is unsupported. Install a supported 0.2.x Engine CLI.";
    case "probe_failed":
    case "probe_timed_out":
    case "malformed_version":
    case "version_unavailable":
      return "CodeStrata CLI version probe failed. Retry detection or follow installation guidance.";
    case "not_found":
    case "not_attempted":
    default:
      return "CodeStrata Engine CLI was not found. Follow installation guidance, then refresh detection. The extension does not install packages automatically.";
  }
}

function baseResult(
  partial: Partial<InstallationGuidanceResult> &
    Pick<InstallationGuidanceResult, "status" | "discovery_status" | "guidance_category">,
  limitations: readonly string[],
  methodCount: number
): InstallationGuidanceResult {
  return {
    status: partial.status,
    discovery_status: partial.discovery_status,
    guidance_category: partial.guidance_category,
    supported_method_count: partial.supported_method_count ?? methodCount,
    user_action_required: partial.user_action_required ?? true,
    rediscovery_available: partial.rediscovery_available ?? true,
    rediscovery_attempted: partial.rediscovery_attempted ?? false,
    rediscovery_outcome: partial.rediscovery_outcome ?? "not_attempted",
    recovery_category: partial.recovery_category ?? partial.guidance_category,
    limitations: [...(partial.limitations ?? limitations)].sort(),
  };
}

/**
 * Run explicit installation guidance. Never installs, downloads, or mutates PATH.
 */
export async function runInstallationGuidance(
  input: RunInstallationGuidanceInput
): Promise<InstallationGuidanceResult> {
  const limitations = input.limitations ?? DEFAULT_INSTALLATION_LIMITATIONS;
  const methods = installationMethodCatalog();
  const methodCount = methods.length;
  const category = mapDiscoveryToGuidanceCategory(input.discoveryStatus);

  if (input.discoveryStatus === "compatible") {
    input.adapters.appendOutputLine(
      "CodeStrata CLI installation guidance not required (compatible)."
    );
    return guidanceNotRequired("compatible");
  }

  input.adapters.appendOutputLine(
    "CodeStrata CLI installation guidance (guidance-only; no automatic install)."
  );

  const primary = await input.adapters.showActions(guidanceMessage(input.discoveryStatus), [
    "Show Installation Options",
    "Refresh CLI Detection",
    "Configure Executable",
    "Cancel",
  ]);

  if (!primary || primary === "Cancel") {
    return baseResult(
      {
        status: "user_cancelled",
        discovery_status: input.discoveryStatus,
        guidance_category: category,
        user_action_required: true,
      },
      limitations,
      methodCount
    );
  }

  if (primary === "Configure Executable") {
    await input.adapters.openExecutableSettings();
    return baseResult(
      {
        status: "action_opened",
        discovery_status: input.discoveryStatus,
        guidance_category: "correct_cli_setting",
        recovery_category: "correct_cli_setting",
      },
      limitations,
      methodCount
    );
  }

  if (primary === "Refresh CLI Detection") {
    const status = await input.adapters.refreshDiscovery();
    const ok = status === "compatible";
    input.adapters.appendOutputLine(
      ok
        ? "CLI rediscovery succeeded."
        : "CLI rediscovery did not find a compatible CLI."
    );
    return baseResult(
      {
        status: ok ? "rediscovery_succeeded" : "rediscovery_failed",
        discovery_status: status,
        guidance_category: ok ? "none" : category,
        recovery_category: ok ? "none" : "retry_discovery",
        user_action_required: !ok,
        rediscovery_attempted: true,
        rediscovery_outcome: ok ? "succeeded" : "failed",
      },
      limitations,
      methodCount
    );
  }

  // Show Installation Options
  const pick = await input.adapters.showQuickPick(
    [
      {
        id: "python_package",
        label: "Copy Python package install command",
        description: "pip (display/copy only)",
      },
      {
        id: "pipx",
        label: "Copy pipx install command",
        description: "pipx (display/copy only)",
      },
      {
        id: "uv_tool",
        label: "Copy uv tool install command",
        description: "uv (display/copy only)",
      },
      {
        id: "terminal_guidance",
        label: "Open terminal",
        description: "Visible terminal; command is not auto-executed",
      },
      {
        id: "documentation",
        label: "Open installation documentation",
        description: "Trusted Engine Quick Start",
      },
    ],
    "CodeStrata CLI installation guidance"
  );

  if (!pick) {
    return baseResult(
      {
        status: "user_cancelled",
        discovery_status: input.discoveryStatus,
        guidance_category: category,
      },
      limitations,
      methodCount
    );
  }

  return executeGuidanceAction({
    methodId: pick as InstallationMethodId,
    discoveryStatus: input.discoveryStatus,
    platform: input.platform,
    adapters: input.adapters,
    category,
    limitations,
    methodCount,
  });
}

async function executeGuidanceAction(options: {
  readonly methodId: InstallationMethodId;
  readonly discoveryStatus: CliDiscoveryStatus | "not_attempted";
  readonly platform: InstallationPlatform;
  readonly adapters: InstallationUiAdapters;
  readonly category: ReturnType<typeof mapDiscoveryToGuidanceCategory>;
  readonly limitations: readonly string[];
  readonly methodCount: number;
}): Promise<InstallationGuidanceResult> {
  const { methodId, adapters, platform } = options;

  if (methodId === "documentation") {
    const ok = await adapters.openExternalUrl(TRUSTED_INSTALLATION_DOCS_URL);
    adapters.appendOutputLine(
      ok
        ? "Opened CodeStrata Engine installation documentation."
        : "Could not open installation documentation."
    );
    return baseResult(
      {
        status: ok ? "action_opened" : "installation_method_unavailable",
        discovery_status: options.discoveryStatus,
        guidance_category: "view_documentation",
        recovery_category: "view_documentation",
      },
      options.limitations,
      options.methodCount
    );
  }

  if (methodId === "terminal_guidance") {
    const ok = await adapters.openTerminal();
    const preview = trustedCommandForMethod("terminal_guidance", platform);
    if (preview) {
      adapters.appendOutputLine(
        "Terminal opened. Paste a trusted install command from Copy options (not auto-executed)."
      );
    }
    return baseResult(
      {
        status: ok ? "terminal_opened" : "installation_method_unavailable",
        discovery_status: options.discoveryStatus,
        guidance_category: options.category,
      },
      options.limitations,
      options.methodCount
    );
  }

  const command = trustedCommandForMethod(methodId, platform);
  if (!command) {
    return baseResult(
      {
        status: "installation_method_unavailable",
        discovery_status: options.discoveryStatus,
        guidance_category: options.category,
      },
      options.limitations,
      options.methodCount
    );
  }

  const copied = await adapters.copyText(command);
  adapters.appendOutputLine(
    copied
      ? "Install command copied to clipboard (not executed by the extension)."
      : "Clipboard copy failed."
  );
  const status: InstallationGuidanceStatus = copied
    ? "command_copied"
    : "installation_method_unavailable";
  return baseResult(
    {
      status,
      discovery_status: options.discoveryStatus,
      guidance_category: options.category,
    },
    options.limitations,
    options.methodCount
  );
}

/** Prove automatic installation is forbidden at the policy boundary. */
export function automaticInstallationAllowed(): false {
  return false;
}
