/** Optional AI setup guidance — never stores credentials in the extension. */

import * as vscode from "vscode";

import { ENGINE_DOCS_QUICK_START } from "../engine/cliContract";

export type AiProviderChoice =
  | "skip"
  | "bedrock"
  | "openai"
  | "azure-openai"
  | "anthropic";

const PROVIDER_DOCS: Record<Exclude<AiProviderChoice, "skip">, string> = {
  bedrock:
    "https://github.com/CodeStrata/codestrata-engine/blob/main/docs/ai-enrichment.md",
  openai:
    "https://github.com/CodeStrata/codestrata-engine/blob/main/docs/ai-enrichment.md",
  "azure-openai":
    "https://github.com/CodeStrata/codestrata-engine/blob/main/docs/ai-enrichment.md",
  anthropic:
    "https://github.com/CodeStrata/codestrata-engine/blob/main/docs/ai-enrichment.md",
};

export async function offerOptionalAiSetup(): Promise<void> {
  const picked = await vscode.window.showQuickPick(
    [
      {
        label: "Skip for now",
        description: "Recommended — deterministic Engineering Assessment is the default",
        value: "skip" as AiProviderChoice,
      },
      {
        label: "Amazon Bedrock",
        description: "Configure in Engine (codestrata.toml / environment)",
        value: "bedrock" as AiProviderChoice,
      },
      {
        label: "OpenAI",
        description: "Configure in Engine — never store keys in extension settings",
        value: "openai" as AiProviderChoice,
      },
      {
        label: "Azure OpenAI",
        description: "Configure in Engine environment / TOML",
        value: "azure-openai" as AiProviderChoice,
      },
      {
        label: "Anthropic",
        description: "Configure in Engine when supported by your Engine version",
        value: "anthropic" as AiProviderChoice,
      },
    ],
    {
      title: "Enable AI Enhancements? (optional)",
      placeHolder: "Credentials stay in CodeStrata Engine — not this extension",
      ignoreFocusOut: true,
    }
  );

  if (!picked || picked.value === "skip") {
    void vscode.window.showInformationMessage(
      "AI skipped. Deterministic Engineering Assessment remains available."
    );
    return;
  }

  await vscode.workspace
    .getConfiguration()
    .update(
      "codestrata.ai.providerHint",
      picked.value === "azure-openai" || picked.value === "anthropic"
        ? "auto"
        : picked.value,
      vscode.ConfigurationTarget.Global
    );

  const open = await vscode.window.showInformationMessage(
    `Configure ${picked.label} in CodeStrata Engine (codestrata.toml / environment). ` +
      "Do not put AI provider secrets or Platform API keys in extension settings.",
    "Open Engine AI Docs",
    "Initialize codestrata.toml",
    "Dismiss"
  );
  if (open === "Open Engine AI Docs") {
    await vscode.env.openExternal(vscode.Uri.parse(PROVIDER_DOCS[picked.value]));
  } else if (open === "Initialize codestrata.toml") {
    await vscode.commands.executeCommand("codestrata.init");
  }
}

export async function openEngineDocs(): Promise<void> {
  await vscode.env.openExternal(vscode.Uri.parse(ENGINE_DOCS_QUICK_START));
}
