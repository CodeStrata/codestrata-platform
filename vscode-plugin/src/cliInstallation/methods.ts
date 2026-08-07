/**
 * Closed installation-method catalog (Slice 13.3 Approach A).
 * Fixed trusted templates only — never executed by the extension.
 */

export const INSTALLATION_METHOD_IDS = [
  "documentation",
  "python_package",
  "pipx",
  "uv_tool",
  "terminal_guidance",
  "unavailable",
] as const;

export type InstallationMethodId = (typeof INSTALLATION_METHOD_IDS)[number];

export type InstallationActionCategory =
  | "open_documentation"
  | "copy_command"
  | "open_terminal"
  | "none";

export type InstallationMethod = {
  readonly id: InstallationMethodId;
  readonly platforms: readonly ("windows" | "macos" | "linux")[];
  readonly action_category: InstallationActionCategory;
  readonly automatic_execution_allowed: false;
  readonly network_required: boolean;
  readonly command_preview_available: boolean;
  readonly verification_required: true;
  readonly limitations: readonly string[];
};

/** Fixed HTTPS documentation URL — no query params, no local state. */
export const TRUSTED_INSTALLATION_DOCS_URL =
  "https://github.com/CodeStrata/codestrata-engine/blob/main/docs/quick-start.md" as const;

/**
 * Fixed install command templates (Approach A — copy/display only).
 * No sudo, no pipe-to-shell, no chained commands, no PATH edits.
 */
export const TRUSTED_COMMAND_TEMPLATES = {
  python_package_posix: 'python3 -m pip install "codestrata[mcp]"',
  python_package_windows: 'py -3 -m pip install "codestrata[mcp]"',
  pipx: 'pipx install "codestrata[mcp]"',
  uv_tool: 'uv tool install "codestrata[mcp]"',
} as const;

export function installationMethodCatalog(): readonly InstallationMethod[] {
  const commonLimitations = [
    "automatic_execution_forbidden",
    "public_package_availability_not_verified_in_slice",
  ] as const;
  return [
    {
      id: "documentation",
      platforms: ["windows", "macos", "linux"],
      action_category: "open_documentation",
      automatic_execution_allowed: false,
      network_required: true,
      command_preview_available: false,
      verification_required: true,
      limitations: [...commonLimitations],
    },
    {
      id: "python_package",
      platforms: ["windows", "macos", "linux"],
      action_category: "copy_command",
      automatic_execution_allowed: false,
      network_required: true,
      command_preview_available: true,
      verification_required: true,
      limitations: [...commonLimitations],
    },
    {
      id: "pipx",
      platforms: ["windows", "macos", "linux"],
      action_category: "copy_command",
      automatic_execution_allowed: false,
      network_required: true,
      command_preview_available: true,
      verification_required: true,
      limitations: [...commonLimitations],
    },
    {
      id: "uv_tool",
      platforms: ["windows", "macos", "linux"],
      action_category: "copy_command",
      automatic_execution_allowed: false,
      network_required: true,
      command_preview_available: true,
      verification_required: true,
      limitations: [...commonLimitations],
    },
    {
      id: "terminal_guidance",
      platforms: ["windows", "macos", "linux"],
      action_category: "open_terminal",
      automatic_execution_allowed: false,
      network_required: false,
      command_preview_available: true,
      verification_required: true,
      limitations: [...commonLimitations, "terminal_does_not_auto_execute"],
    },
  ];
}

export function trustedCommandForMethod(
  methodId: InstallationMethodId,
  platform: "windows" | "macos" | "linux"
): string | undefined {
  switch (methodId) {
    case "python_package":
      return platform === "windows"
        ? TRUSTED_COMMAND_TEMPLATES.python_package_windows
        : TRUSTED_COMMAND_TEMPLATES.python_package_posix;
    case "pipx":
      return TRUSTED_COMMAND_TEMPLATES.pipx;
    case "uv_tool":
      return TRUSTED_COMMAND_TEMPLATES.uv_tool;
    case "terminal_guidance":
      return platform === "windows"
        ? TRUSTED_COMMAND_TEMPLATES.python_package_windows
        : TRUSTED_COMMAND_TEMPLATES.python_package_posix;
    default:
      return undefined;
  }
}

export function methodCatalogToStableDict(): Record<string, unknown>[] {
  return installationMethodCatalog().map((method) => ({
    action_category: method.action_category,
    automatic_execution_allowed: method.automatic_execution_allowed,
    command_preview_available: method.command_preview_available,
    id: method.id,
    limitations: [...method.limitations].sort(),
    network_required: method.network_required,
    platforms: [...method.platforms].sort(),
    verification_required: method.verification_required,
  }));
}
