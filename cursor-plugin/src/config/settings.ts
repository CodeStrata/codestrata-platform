/**
 * Extension settings — thin VS Code wrappers over Engine CLI flags.
 * Does not invent a parallel configuration model for Engineering Intelligence.
 */

export type FindingsGroupBy = "domain" | "severity" | "file" | "rule";
export type AiProviderHint = "auto" | "bedrock" | "openai" | "none";

export interface CodestrataSettings {
  executable: string;
  outputDirectory: string;
  configPath: string;
  defaultNoAi: boolean;
  extraArgs: string[];
  groupBy: FindingsGroupBy;
  aiProviderHint: AiProviderHint;
}

export const DEFAULT_SETTINGS: CodestrataSettings = {
  executable: "codestrata",
  outputDirectory: "reports",
  configPath: "",
  defaultNoAi: true,
  extraArgs: [],
  groupBy: "severity",
  aiProviderHint: "auto",
};

export function normalizeSettings(
  raw: Partial<CodestrataSettings> | Record<string, unknown>
): CodestrataSettings {
  const groupBy = String(raw.groupBy ?? DEFAULT_SETTINGS.groupBy);
  const validGroup: FindingsGroupBy[] = ["domain", "severity", "file", "rule"];
  const hint = String(raw.aiProviderHint ?? DEFAULT_SETTINGS.aiProviderHint);
  const validHint: AiProviderHint[] = ["auto", "bedrock", "openai", "none"];
  return {
    executable: String(raw.executable ?? DEFAULT_SETTINGS.executable).trim() || "codestrata",
    outputDirectory:
      String(raw.outputDirectory ?? DEFAULT_SETTINGS.outputDirectory).trim() || "reports",
    configPath: String(raw.configPath ?? "").trim(),
    defaultNoAi: Boolean(
      raw.defaultNoAi === undefined ? DEFAULT_SETTINGS.defaultNoAi : raw.defaultNoAi
    ),
    extraArgs: Array.isArray(raw.extraArgs)
      ? raw.extraArgs.map((item) => String(item))
      : [],
    groupBy: (validGroup.includes(groupBy as FindingsGroupBy)
      ? groupBy
      : DEFAULT_SETTINGS.groupBy) as FindingsGroupBy,
    aiProviderHint: (validHint.includes(hint as AiProviderHint)
      ? hint
      : DEFAULT_SETTINGS.aiProviderHint) as AiProviderHint,
  };
}

export function readSettingsFromWorkspaceConfig(get: (key: string) => unknown): CodestrataSettings {
  return normalizeSettings({
    executable: get("codestrata.engine.executable"),
    outputDirectory: get("codestrata.assessment.outputDirectory"),
    configPath: get("codestrata.assessment.configPath"),
    defaultNoAi: get("codestrata.assessment.defaultNoAi"),
    extraArgs: get("codestrata.assessment.extraArgs"),
    groupBy: get("codestrata.findings.groupBy"),
    aiProviderHint: get("codestrata.ai.providerHint"),
  });
}
