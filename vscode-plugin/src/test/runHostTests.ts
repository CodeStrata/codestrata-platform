/**
 * VS Code Extension Host test entry.
 *
 * Requires network to download a VS Code build the first time.
 * Run: npm run test:host
 *
 * If the host cannot launch in this environment, unit tests remain the
 * primary gate; this harness is still prepared for CI / local F5 validation.
 */

import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

import { runTests } from "@vscode/test-electron";

async function main(): Promise<void> {
  const extensionDevelopmentPath = path.resolve(__dirname, "../../");
  const extensionTestsPath = path.resolve(__dirname, "./suite/index");

  // macOS AF_UNIX paths are capped (~103 chars). Keep user-data short.
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "cs-vsc-"));

  // ELECTRON_RUN_AS_NODE causes the Code/Electron binary to treat VS Code CLI
  // flags as Node options ("bad option: --extensionDevelopmentPath").
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
  console.error("Hosted VS Code tests failed to launch:");
  console.error(error);
  console.error(
    "Limitation: Extension Host tests require downloading VS Code via @vscode/test-electron. " +
      "Unit tests (npm test) still validate contracts. Use F5 Extension Host locally when available."
  );
  process.exit(1);
});
