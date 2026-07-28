# CodeStrata Cursor Extension (Community Edition)

**Engineering Intelligence for Modern Software Organizations** — bring deterministic
**CodeStrata Engine** Engineering Assessments into **Cursor** Chat / Agent.

```text
CodeStrata Cursor Extension
        ↓
CodeStrata Engine CLI
        ↓
Public assessment artifacts
        ↓
.cursor/rules/codestrata-engineering.mdc
        ↓
Cursor Chat / Agent
```

This extension is a **thin client**. It does **not** independently analyze source code.
**CodeStrata Engine** performs the assessment. The extension consumes **public** report
artifacts and projects them into a generated Cursor rule.

**Canonical documentation:** [https://docs.codestrata.ai/extensions/cursor](https://docs.codestrata.ai/extensions/cursor)  
(Monorepo docs portal path: `docs/extensions/cursor.md` →
[https://docs.codestrata.ai/extensions/cursor](https://docs.codestrata.ai/extensions/cursor))

Cursor answers may still include model inference. CodeStrata findings must **not** be
invented. Inspect source before applying changes.

## Prerequisites

- Cursor (VS Code API `^1.85.0` compatible)
- Python 3.12+
- CodeStrata Engine (`codestrata`)

See [COMPATIBILITY.md](COMPATIBILITY.md).

## Installation

1. Install **CodeStrata for Cursor** from the Marketplace (or Install from VSIX).
2. Open a **trusted** repository folder.
3. On first run, detect/install Engine, then run an Engineering Assessment.

```bash
# Manual Engine install (if needed)
python -m pip install --user 'codestrata[mcp]'
codestrata version
```

## First journey

1. Install extension → open repository.
2. Verify or **Install CodeStrata Engine**.
3. **CodeStrata: Engineering Assessment** (deterministic / `--no-ai` by default).
4. Confirm `.cursor/rules/codestrata-engineering.mdc` is generated.
5. Open Cursor Chat or Agent.
6. Use a **Suggested Question** or **Copy Conversation Prompt** (clipboard is reliable;
   direct Chat insertion is best-effort only).
7. Ask: *What are the highest-priority engineering risks in this repository?*
8. Open the HTML report; refresh when the repo changes.

## Generated Cursor rule

Path: `.cursor/rules/codestrata-engineering.mdc`

| Event | Behavior |
| ----- | -------- |
| Assessment success / Refresh | Create or atomically replace CodeStrata-managed rule |
| Clear Assessment | Remove only the CodeStrata-managed file |
| User rules | Sibling `.cursor/rules/*` files are preserved |

**Recommended default (Option A):** treat the file as a **local generated artifact**
and add it to `.gitignore` if you do not want assessment snapshots in git.

**Option B:** commit intentionally for shared team context.

The extension never silently edits `.gitignore`. Review generated context before
committing. Truncation and grounding limitations are stated inside the rule.

## Engine discovery & install

Order: configured executable → workspace `.venv` → active Python → `PATH`.  
Install mechanisms: `uv tool` / `pipx` / `pip --user` (official Quick Start family).  
Failures keep the extension active with Install / Configure / Docs / Output actions.

## Commands

| Command | Purpose |
| ------- | ------- |
| Engineering Assessment | Deterministic assess |
| Engineering Assessment with AI | Optional Engine AI |
| Refresh / Clear Assessment | Reload or remove context + managed rule |
| Install CodeStrata Engine | Guided install |
| Check CodeStrata Environment | Discovery + doctor |
| Show Welcome / First Run | Replay onboarding |
| Open Report | `report.html` |
| Show Findings / Recommendations | From public artifacts |
| Copy Conversation Prompt | Clipboard grounded prompt |
| Open Documentation / Output | Docs + logs |

## Settings

Reuse Engine `codestrata.toml`. Extension settings only pass CLI flags
(`codestrata.engine.executable`, output directory, config path, default `--no-ai`).

## Optional AI

Engine providers only (Bedrock / OpenAI / Azure OpenAI / Anthropic).  
Credentials never stored in extension settings. Not Platform keys.

## Multi-root & trust

Multi-root: pick one repository. Context is scoped to that root.  
Untrusted workspaces: Engine and rule writes are blocked until trusted.

## Privacy & security

See [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md).  
No Platform APIs · no extension telemetry · secrets redacted · shell disabled.

CodeStrata does **not** govern Cursor’s own privacy/model controls.

## Community scope

Local Engine · local assessments · optional AI.  
**Not included:** Platform, Portfolio Intelligence, Executive Intelligence, Repository Retrieval.

## Troubleshooting

| Symptom | Action |
| ------- | ------ |
| Engine not found | Install Engine / configure executable |
| Suggested prompts disabled | Run Engineering Assessment |
| Stale Chat answers | Refresh Assessment |
| Chat not opened automatically | Paste copied prompt |
| Untrusted workspace | Manage Workspace Trust |

## Known limitations

- Automated tests use VS Code Extension Host (Cursor-compatible APIs), not the Cursor IDE binary.
- Cursor Chat command IDs vary; clipboard copy is the reliable transfer path.
- Live Chat grounding must be validated manually ([RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)).
- Windows/Linux install matrix not claimed unless run.
- Assessment context reduces hallucination risk; it cannot eliminate model inference.

## Development

```bash
npm install
npm test
npm run test:host
npm run package:dry
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [EXTRACTION.md](EXTRACTION.md), [CI.md](CI.md).

Engine docs: https://github.com/sknampally/codestrata-engine/blob/main/docs/quick-start.md
