/**
 * VS Code Extension Host harness (Cursor-compatible APIs).
 * Does not claim native Cursor IDE automation — use F5 / manual Cursor for that.
 */

import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

import { runTests } from "@vscode/test-electron";

async function main(): Promise<void> {
  const extensionDevelopmentPath = path.resolve(__dirname, "../../");
  const extensionTestsPath = path.resolve(__dirname, "./suite/index");
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "cs-cur-"));
  const extensionTestsEnv = { ...process.env };
  delete extensionTestsEnv.ELECTRON_RUN_AS_NODE;

  await runTests({
    extensionDevelopmentPath,
    extensionTestsPath,
    launchArgs: ["--disable-extensions", `--user-data-dir=${userDataDir}`],
    extensionTestsEnv,
  });
}

main().catch((error) => {
  console.error("Hosted extension tests failed to launch:");
  console.error(error);
  console.error(
    "Limitation: automated host uses VS Code via @vscode/test-electron. " +
      "Validate Chat/Agent grounding manually inside Cursor."
  );
  process.exit(1);
});
