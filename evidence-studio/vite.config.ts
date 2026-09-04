import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { basename, resolve } from "node:path";

const outputDirectory = resolve(
  __dirname,
  "../engine/src/codestrata/interfaces/evidence_studio/assets",
);

function thirdPartyNotices() {
  return {
    name: "codestrata-third-party-notices",
    closeBundle() {
      copyFileSync(
        resolve(__dirname, "THIRD_PARTY_NOTICES.md"),
        resolve(outputDirectory, "THIRD_PARTY_NOTICES.md"),
      );
      const lock = JSON.parse(readFileSync(resolve(__dirname, "package-lock.json"), "utf8"));
      const sections: string[] = [];
      for (const [packagePath, metadata] of Object.entries<any>(lock.packages).sort()) {
        if (!packagePath.startsWith("node_modules/") || metadata.dev || !metadata.version) continue;
        const directory = resolve(__dirname, packagePath);
        const candidates = ["LICENSE", "LICENSE.md", "LICENSE.txt", "license", "license.md"];
        for (const candidate of candidates) {
          try {
            const license = readFileSync(resolve(directory, candidate), "utf8").trim();
            const packageName = metadata.name ?? packagePath.replace(/^node_modules\//, "");
            sections.push(`${"=".repeat(78)}\n${packageName}@${metadata.version} · ${basename(candidate)}\n${"=".repeat(78)}\n${license}`);
            break;
          } catch {
            // Some package metadata points at platform-optional packages not installed here.
          }
        }
      }
      const licenseDirectory = resolve(outputDirectory, "licenses");
      mkdirSync(licenseDirectory, { recursive: true });
      writeFileSync(
        resolve(licenseDirectory, "THIRD_PARTY_LICENSES.txt"),
        `${sections.join("\n\n")}\n`,
        "utf8",
      );
    },
  };
}

export default defineConfig({
  plugins: [react(), thirdPartyNotices()],
  build: {
    outDir: outputDirectory,
    emptyOutDir: true,
    sourcemap: false,
  },
});
