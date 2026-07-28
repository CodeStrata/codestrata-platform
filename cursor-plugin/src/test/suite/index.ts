import * as assert from "node:assert/strict";

import * as vscode from "vscode";

export async function run(): Promise<void> {
  const extension = vscode.extensions.getExtension("codestrata.codestrata-cursor");
  assert.ok(extension, "extension not found (publisher.name)");
  await extension.activate();
  assert.equal(extension.isActive, true);

  const commands = await vscode.commands.getCommands(true);
  for (const command of [
    "codestrata.assess",
    "codestrata.refreshAssessment",
    "codestrata.clearAssessment",
    "codestrata.installEngine",
    "codestrata.checkEnvironment",
    "codestrata.showWelcome",
    "codestrata.copyConversationPrompt",
    "codestrata.openHtmlReport",
  ]) {
    assert.ok(commands.includes(command), `missing command ${command}`);
  }

  assert.equal(
    typeof vscode.workspace.getConfiguration().get("codestrata.engine.executable"),
    "string"
  );
  console.log("CodeStrata Cursor hosted Extension Host checks passed (VS Code-compatible APIs).");
}
