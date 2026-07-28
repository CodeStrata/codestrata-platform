import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { describe, it } from "node:test";

import { normalizeSettings } from "../config/settings";
import {
  buildConversationContext,
  orderFindings,
  selectFindingsForContext,
} from "../conversation/context";
import {
  clearCursorConversationRule,
  GENERATED_FILE_MARKER,
  isCodestrataManagedRule,
  listSiblingCursorRules,
  renderCursorRule,
  writeCursorConversationRule,
} from "../conversation/cursorRules";
import {
  constructPrompt,
  constructPromptWithoutAssessment,
} from "../conversation/prompts";
import { classifyEnginePresence } from "../onboarding/state";
import { SUGGESTED_QUESTIONS, questionsByCategory } from "../conversation/suggestedQuestions";
import { buildAssessArgs, parseJsonSummary } from "../engine/cliContract";
import { runCodestrataCli } from "../engine/cliRunner";
import {
  isCompatibleEngineVersion,
  parseEngineVersionOutput,
} from "../engine/compatibility";
import { listEngineCandidates, redactSecrets } from "../engine/discovery";
import { detectPlatform, selectInstallMethods } from "../engine/installer";
import {
  loadArtifactsFromRunDirectory,
  normalizeFindings,
} from "../reports/parser";
import { checkReportSchemaVersion } from "../reports/schema";

function fixtureArtifacts(extraFindings = 0) {
  const findings = [
    {
      id: "1",
      title: "Critical arch",
      severity: "critical",
      category: "architecture",
      rule_id: "AR-001",
      evidence: [{ path: "src/a.ts", excerpt: "line: 1" }],
    },
    {
      id: "2",
      title: "Dep issue",
      severity: "high",
      category: "dependencies",
      rule_id: "DEP-1",
    },
    {
      id: "3",
      title: "Low noise",
      severity: "low",
      category: "architecture",
    },
  ];
  for (let index = 0; index < extraFindings; index += 1) {
    findings.push({
      id: `x${index}`,
      title: `Extra ${index}`,
      severity: "info",
      category: `domain-${index % 5}`,
      rule_id: `R-${index}`,
    });
  }
  return {
    runDirectory: "/workspace/reports/app/run1",
    htmlReportPath: "/workspace/reports/app/run1/report.html",
    findings: normalizeFindings({ findings }),
    recommendations: [
      {
        id: "r1",
        title: "Modernize module",
        priority: "P1",
        related_finding_ids: ["1"],
        actions: ["Inspect src/a.ts", "Refactor"],
      },
    ],
    manifest: { schema_version: "1.2" },
    parseWarnings: [] as string[],
  };
}

describe("settings and assessment args", () => {
  it("defaults to deterministic assess", () => {
    const settings = normalizeSettings({});
    assert.equal(settings.defaultNoAi, true);
    const args = buildAssessArgs({
      workspaceFolder: "/repo with spaces",
      withAi: false,
      settings,
    });
    assert.ok(args.includes("--no-ai"));
    assert.ok(args.includes("/repo with spaces"));
  });

  it("parses json summary", () => {
    const summary = parseJsonSummary(
      '{"run_directory":"reports/a/1","html_report":"report.html","findings":2}\n'
    );
    assert.equal(summary?.run_directory, "reports/a/1");
  });
});

describe("engine discovery and compatibility", () => {
  it("lists discovery candidates including path", () => {
    const candidates = listEngineCandidates("codestrata", []);
    assert.ok(candidates.some((item) => item.source === "path"));
  });

  it("parses version and rejects major 2", () => {
    const info = parseEngineVersionOutput("CodeStrata 0.1.0\nCLI: 0.1.0\n");
    assert.equal(info.compatible, true);
    assert.equal(isCompatibleEngineVersion("2.0.0"), false);
  });

  it("selects install methods without shell metacharacters", () => {
    assert.ok(["windows", "macos", "linux"].includes(detectPlatform()));
    for (const method of selectInstallMethods()) {
      assert.ok(!method.args.join(" ").includes(";"));
      assert.ok(method.args.some((token) => token.includes("codestrata")));
    }
  });

  it("redacts secrets", () => {
    assert.doesNotMatch(redactSecrets("OPENAI_API_KEY=sk-secret"), /sk-secret/);
  });
});

describe("process cancellation", () => {
  it("cancels a long-running child process", async () => {
    const controller = new AbortController();
    const pending = runCodestrataCli({
      executable: process.execPath,
      args: ["-e", "setInterval(() => {}, 1000)"],
      cwd: process.cwd(),
      signal: controller.signal,
    });
    controller.abort();
    const result = await pending;
    assert.equal(result.cancelled, true);
  });
});

describe("report compatibility", () => {
  it("accepts schema 1.2 and rejects other majors", () => {
    assert.equal(checkReportSchemaVersion("1.2").ok, true);
    assert.equal(checkReportSchemaVersion("2.0").ok, false);
  });

  it("tolerates malformed JSON without throwing", () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "cs-mal-"));
    fs.writeFileSync(path.join(tmp, "report.json"), "{not-json");
    const artifacts = loadArtifactsFromRunDirectory(tmp);
    assert.ok(artifacts.parseWarnings.length >= 1);
  });

  it("loads empty findings safely", () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "cs-empty-"));
    fs.writeFileSync(
      path.join(tmp, "report.json"),
      JSON.stringify({ manifest: { schema_version: "1.2" }, findings: [] })
    );
    const artifacts = loadArtifactsFromRunDirectory(tmp);
    assert.equal(artifacts.findings.length, 0);
  });
});

describe("conversation context quality", () => {
  it("orders by severity and preserves domain diversity when truncating", () => {
    const ordered = orderFindings(fixtureArtifacts().findings);
    assert.equal(ordered[0].severity, "critical");
    const many = fixtureArtifacts(80);
    const selected = selectFindingsForContext(many.findings, 20);
    assert.equal(selected.truncated, true);
    assert.ok(selected.selected.length <= 20);
    assert.ok(selected.selected.some((item) => item.severity === "critical"));
  });

  it("builds grounded markdown with limitations and report path", () => {
    const context = buildConversationContext(fixtureArtifacts(), {
      workspaceFolder: "/workspace",
      repositoryLabel: "app",
      engineVersion: "0.1.0",
    });
    assert.match(context.markdown, /Grounding rules/);
    assert.match(context.markdown, /Absence of a finding/);
    assert.match(context.markdown, /report\.html/);
    assert.match(context.markdown, /Engine version: 0\.1\.0/);
    assert.doesNotMatch(context.markdown, /function |class /);
  });
});

describe("cursor rule lifecycle", () => {
  it("writes atomically with marker, skips unchanged, preserves user rules", () => {
    const workspace = fs.mkdtempSync(
      path.join(__dirname, "..", "..", ".tmp-test-")
    );
    try {
      const rulesDir = path.join(workspace, ".cursor", "rules");
      fs.mkdirSync(rulesDir, { recursive: true });
      const userRule = path.join(rulesDir, "my-team.mdc");
      fs.writeFileSync(userRule, "user rule", "utf8");

      const context = buildConversationContext(fixtureArtifacts(), {
        workspaceFolder: workspace,
        repositoryLabel: "demo",
        engineVersion: "0.1.0",
      });
      const first = writeCursorConversationRule(workspace, context);
      assert.equal(first.wrote, true);
      const contents = fs.readFileSync(first.path, "utf8");
      assert.ok(isCodestrataManagedRule(contents));
      assert.match(contents, new RegExp(GENERATED_FILE_MARKER));
      assert.match(renderCursorRule(context), /fingerprint:/);

      const second = writeCursorConversationRule(workspace, context);
      assert.equal(second.wrote, false);

      assert.ok(listSiblingCursorRules(workspace).some((p) => p.endsWith("my-team.mdc")));
      const cleared = clearCursorConversationRule(workspace);
      assert.equal(cleared.removed, true);
      assert.ok(fs.existsSync(userRule));
    } finally {
      fs.rmSync(workspace, { recursive: true, force: true });
    }
  });

  it("refuses to overwrite a foreign rule file", () => {
    const workspace = fs.mkdtempSync(
      path.join(__dirname, "..", "..", ".tmp-test-")
    );
    try {
      const target = path.join(workspace, ".cursor", "rules", "codestrata-engineering.mdc");
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, "foreign content without marker", "utf8");
      const context = buildConversationContext(fixtureArtifacts(), {
        workspaceFolder: workspace,
      });
      assert.throws(() => writeCursorConversationRule(workspace, context), /Refusing/);
    } finally {
      fs.rmSync(workspace, { recursive: true, force: true });
    }
  });
});

describe("prompt UX", () => {
  it("constructs assessment-grounded prompts and blocks inventing without assessment", () => {
    const context = buildConversationContext(fixtureArtifacts());
    const prompt = constructPrompt(context, "What are the highest-priority findings?");
    assert.equal(prompt.hasAssessment, true);
    assert.match(prompt.fullPrompt, /AR-001/);
    const missing = constructPromptWithoutAssessment("Invent findings");
    assert.equal(missing.hasAssessment, false);
    assert.match(missing.fullPrompt, /No valid CodeStrata Engineering Assessment/);
  });

  it("categorizes suggested questions", () => {
    assert.ok(SUGGESTED_QUESTIONS.length >= 10);
    assert.ok(questionsByCategory().has("Prioritize"));
    assert.ok(questionsByCategory().has("Validate"));
  });
});

describe("onboarding and package metadata", () => {
  it("classifies Engine presence for first-run branches", () => {
    assert.equal(classifyEnginePresence({ found: false }), "missing");
    assert.equal(classifyEnginePresence({ found: true, compatible: false }), "incompatible");
    assert.equal(classifyEnginePresence({ found: true, compatible: true }), "ready");
  });

  it("keeps Community display metadata consistent", () => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const pkg = require("../../package.json") as {
      name: string;
      displayName: string;
      version: string;
      publisher: string;
      engines: { vscode: string };
      description: string;
    };
    assert.equal(pkg.name, "codestrata-cursor");
    assert.equal(pkg.displayName, "CodeStrata");
    assert.match(pkg.version, /^0\.2\./);
    assert.equal(pkg.publisher, "codestrata");
    assert.equal(pkg.engines.vscode, "^1.85.0");
    assert.match(pkg.description, /Community Edition/);
    assert.doesNotMatch(pkg.description, /CodeStrata AI|Enterprise Edition/);
  });
});
