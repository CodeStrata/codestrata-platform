import * as assert from "node:assert/strict";

import * as vscode from "vscode";

export async function run(): Promise<void> {
  const extension = vscode.extensions.getExtension("CodeStrataAI.codestrata-assessment");
  assert.ok(extension, "extension not found (publisher.name in package.json)");
  await extension.activate();
  assert.equal(extension.isActive, true);

  const commands = await vscode.commands.getCommands(true);
  for (const command of [
    "codestrata.assess",
    "codestrata.assessWithAi",
    "codestrata.installEngine",
    "codestrata.showWelcome",
    "codestrata.checkEnvironment",
    "codestrata.openHtmlReport",
    "codestrata.publishCurrentReport",
    "codestrata.refreshFindings",
    "codestrata.refreshRecommendations",
    "codestrata.clearResults",
    "codestrata.openOutput",
    "codestrata.openDocumentation",
    "codestrata.init",
  ]) {
    assert.ok(commands.includes(command), `missing command ${command}`);
  }

  const executable = vscode.workspace
    .getConfiguration()
    .get("codestrata.engine.executable");
  assert.equal(typeof executable, "string");

  const groupBy = vscode.workspace.getConfiguration().get("codestrata.findings.groupBy");
  assert.equal(typeof groupBy, "string");

  console.log("CodeStrata hosted Extension Host checks passed.");
}
