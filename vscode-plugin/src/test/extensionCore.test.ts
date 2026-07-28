import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { describe, it } from "node:test";

import {
  normalizeSettings,
  readSettingsFromWorkspaceConfig,
} from "../config/settings";
import {
  aiOptionalGuidance,
  buildAssessArgs,
  parseJsonSummary,
  sanitizeExtraArgs,
} from "../engine/cliContract";
import { runCodestrataCli } from "../engine/cliRunner";
import {
  formatCandidateLabel,
  listEngineCandidates,
  redactSecrets,
} from "../engine/discovery";
import {
  isCompatibleEngineVersion,
  parseEngineVersionOutput,
} from "../engine/compatibility";
import { detectPlatform, selectInstallMethods } from "../engine/installer";
import { filterFindings, groupFindings } from "../reports/findingsModel";
import {
  loadArtifactsFromRunDirectory,
  normalizeFindings,
  normalizeRecommendations,
} from "../reports/parser";
import { checkReportSchemaVersion } from "../reports/schema";
import {
  extractEvidenceLine,
  resolveWorkspaceRelativePath,
} from "../workspace/paths";

describe("settings", () => {
  it("applies defaults", () => {
    const settings = normalizeSettings({});
    assert.equal(settings.executable, "codestrata");
    assert.equal(settings.defaultNoAi, true);
    assert.equal(settings.groupBy, "severity");
  });

  it("reads workspace configuration keys", () => {
    const settings = readSettingsFromWorkspaceConfig((key) => {
      if (key === "codestrata.engine.executable") {
        return "/usr/local/bin/codestrata";
      }
      if (key === "codestrata.findings.groupBy") {
        return "rule";
      }
      if (key === "codestrata.assessment.defaultNoAi") {
        return false;
      }
      return undefined;
    });
    assert.equal(settings.executable, "/usr/local/bin/codestrata");
    assert.equal(settings.groupBy, "rule");
    assert.equal(settings.defaultNoAi, false);
  });
});

describe("cli contract", () => {
  it("builds deterministic assess args with spaces-safe repo path", () => {
    const args = buildAssessArgs({
      workspaceFolder: "/tmp/my repo",
      withAi: false,
      settings: normalizeSettings({
        outputDirectory: "out reports",
        configPath: "codestrata.toml",
        extraArgs: ["--verbose", "--repo", "/evil", "--json-summary"],
      }),
    });
    assert.equal(args[2], "/tmp/my repo");
    assert.equal(args[4], "out reports");
    assert.ok(args.includes("--no-ai"));
    assert.ok(args.includes("--verbose"));
    assert.equal(args.filter((token) => token === "--repo").length, 1);
    assert.equal(args.filter((token) => token === "--json-summary").length, 1);
  });

  it("sanitizes protected extra args", () => {
    const cleaned = sanitizeExtraArgs([
      "--verbose",
      "--output",
      "other",
      "--with-ai",
      "--profile",
      "local",
    ]);
    assert.deepEqual(cleaned, ["--verbose", "--profile", "local"]);
  });

  it("parses json summary from stdout", () => {
    const summary = parseJsonSummary(
      'noise\n{"run_directory":"reports/app/1","html_report":"reports/app/1/report.html","findings":3,"ai_status":"not requested"}\n'
    );
    assert.equal(summary?.findings, 3);
    assert.equal(summary?.ai_status, "not requested");
  });

  it("explains optional AI without Platform keys", () => {
    const text = aiOptionalGuidance("bedrock");
    assert.match(text, /optional/i);
    assert.match(text, /Platform API keys/);
  });
});

describe("engine discovery", () => {
  it("lists configured, venv, active-python, and path candidates", () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "cs-ext-"));
    const bin = path.join(tmp, ".venv", process.platform === "win32" ? "Scripts" : "bin");
    fs.mkdirSync(bin, { recursive: true });
    const exe = path.join(
      bin,
      process.platform === "win32" ? "codestrata.exe" : "codestrata"
    );
    fs.writeFileSync(exe, "");
    const activeRoot = fs.mkdtempSync(path.join(os.tmpdir(), "cs-active-"));
    const activeBin = path.join(
      activeRoot,
      process.platform === "win32" ? "Scripts" : "bin"
    );
    fs.mkdirSync(activeBin, { recursive: true });
    const activeExe = path.join(
      activeBin,
      process.platform === "win32" ? "codestrata.exe" : "codestrata"
    );
    fs.writeFileSync(activeExe, "");
    const previous = process.env.VIRTUAL_ENV;
    process.env.VIRTUAL_ENV = activeRoot;
    try {
      const candidates = listEngineCandidates("/opt/codestrata", [tmp]);
      assert.ok(candidates.some((item) => item.source === "configured"));
      assert.ok(candidates.some((item) => item.source === "workspace-venv"));
      assert.ok(candidates.some((item) => item.source === "active-python"));
      assert.ok(candidates.some((item) => item.source === "path"));
      assert.match(formatCandidateLabel(candidates[0]), /\(/);
    } finally {
      if (previous === undefined) {
        delete process.env.VIRTUAL_ENV;
      } else {
        process.env.VIRTUAL_ENV = previous;
      }
    }
  });

  it("redacts secrets from logs", () => {
    assert.match(
      redactSecrets("Authorization: Bearer super-secret-token"),
      /\*\*\*/
    );
    assert.doesNotMatch(
      redactSecrets("OPENAI_API_KEY=sk-abc123"),
      /sk-abc123/
    );
  });
});

describe("engine compatibility and install planning", () => {
  it("parses codestrata version output", () => {
    const info = parseEngineVersionOutput("CodeStrata 0.1.0\nCLI: 0.1.0\n");
    assert.equal(info.version, "0.1.0");
    assert.equal(info.compatible, true);
    assert.equal(isCompatibleEngineVersion("0.1.0"), true);
    assert.equal(isCompatibleEngineVersion("2.0.0"), false);
  });

  it("selects install methods for the current platform", () => {
    const platform = detectPlatform();
    assert.ok(["windows", "macos", "linux"].includes(platform));
    const methods = selectInstallMethods();
    // At least one method when Python is present in CI/dev machines.
    assert.ok(Array.isArray(methods));
    for (const method of methods) {
      assert.ok(method.args.includes("codestrata[mcp]") || method.args.some((a) => a.includes("codestrata")));
      assert.ok(!method.args.join(" ").includes(";"));
    }
  });
});

describe("process cancellation", () => {
  it("cancels a long-running child process", async () => {
    const controller = new AbortController();
    const pending = runCodestrataCli({
      executable: process.execPath,
      args: ["-e", "setTimeout(() => {}, 30000)"],
      cwd: process.cwd(),
      signal: controller.signal,
    });
    controller.abort();
    const result = await pending;
    assert.equal(result.cancelled, true);
  });
});

describe("report parsing and schema", () => {
  it("normalizes findings and recommendations", () => {
    const findings = normalizeFindings({
      findings: [
        {
          id: "f1",
          title: "Missing CI",
          severity: "Low",
          category: "build",
          rule_id: "rule-ci",
          evidence: [{ path: "package.json" }],
          unknown_additive_field: true,
        },
      ],
    });
    assert.equal(findings.length, 1);
    assert.equal(findings[0].severity, "low");

    const recommendations = normalizeRecommendations({
      assessment: {
        deterministic_recommendations: [
          {
            id: "r1",
            title: "Add CI",
            priority: "high",
            rationale: "Automate checks",
            related_finding_ids: ["f1"],
            extra_future_field: 1,
          },
        ],
      },
    });
    assert.equal(recommendations[0].rationale, "Automate checks");
  });

  it("accepts schema 1.2 and rejects other majors", () => {
    assert.equal(checkReportSchemaVersion("1.2").ok, true);
    assert.equal(checkReportSchemaVersion("1.9").ok, true);
    assert.equal(checkReportSchemaVersion("2.0").ok, false);
  });

  it("loads sample-reports and tolerates missing optional files", () => {
    const runDir = path.resolve(
      __dirname,
      "../../../test-fixtures/sample-reports/javascript"
    );
    const artifacts = loadArtifactsFromRunDirectory(runDir);
    assert.ok(artifacts.findings.length > 0);
    assert.ok(Array.isArray(artifacts.parseWarnings));
  });

  it("reports malformed JSON without throwing", () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "cs-bad-"));
    fs.writeFileSync(path.join(tmp, "report.json"), "{not-json");
    const artifacts = loadArtifactsFromRunDirectory(tmp);
    assert.ok(artifacts.parseWarnings.some((item) => /Malformed JSON/i.test(item)));
  });
});

describe("findings model", () => {
  const sample = normalizeFindings({
    findings: [
      {
        id: "1",
        title: "A",
        severity: "high",
        category: "security",
        rule_id: "r-a",
        evidence: [{ path: "a.ts" }],
      },
      {
        id: "2",
        title: "B",
        severity: "low",
        category: "security",
        rule_id: "r-b",
        evidence: [{ path: "b.ts" }],
      },
      {
        id: "3",
        title: "C",
        severity: "high",
        category: "build",
        rule_id: "r-a",
        evidence: [],
      },
    ],
  });

  it("groups by severity, domain, file, and rule", () => {
    assert.equal(groupFindings(sample, "severity")[0].key, "high");
    assert.equal(groupFindings(sample, "domain").length, 2);
    assert.ok(groupFindings(sample, "file").some((group) => group.key === "a.ts"));
    assert.equal(
      groupFindings(sample, "rule").find((group) => group.key === "r-a")?.findings
        .length,
      2
    );
  });

  it("filters by query", () => {
    assert.equal(filterFindings(sample, "security").length, 2);
  });
});

describe("workspace paths", () => {
  it("keeps relative paths inside workspace and blocks escapes", () => {
    const root = path.resolve("/tmp/workspace root");
    const ok = resolveWorkspaceRelativePath(root, "src/app.ts");
    assert.equal(ok?.insideWorkspace, true);
    const escape = resolveWorkspaceRelativePath(root, "../outside.ts");
    assert.equal(escape?.insideWorkspace, false);
  });

  it("extracts line numbers from excerpts", () => {
    assert.equal(extractEvidenceLine("line: 42 something"), 42);
    assert.equal(extractEvidenceLine("L17: code"), 17);
    assert.equal(extractEvidenceLine("no line here"), undefined);
  });
});
