# CodeStrata VS Code Extension (Community Edition)

**Engineering Intelligence for Modern Software Organizations** — run local
**Engineering Assessments** with **CodeStrata Engine** without leaving VS Code.

```text
VS Code Extension
        ↓
CodeStrata Engine CLI
        ↓
Public JSON summary + report artifacts
        ↓
Findings · Recommendations · Diagnostics · HTML report
```

This extension is a **thin client**. It does not duplicate Engineering Intelligence,
import Engine Python modules, or use CodeStrata Platform APIs.

**Canonical documentation:** [https://docs.codestrata.ai/extensions/vscode](https://docs.codestrata.ai/extensions/vscode)  
(Monorepo docs portal path: `docs/extensions/vscode.md` →
[https://docs.codestrata.ai/extensions/vscode](https://docs.codestrata.ai/extensions/vscode))

![Findings explorer](media/screenshot-findings.png)

### Marketplace screenshots

| | |
| --- | --- |
| Activity | ![Activity](media/screenshot-activity.png) |
| Findings | ![Findings](media/screenshot-findings.png) |
| Recommendations | ![Recommendations](media/screenshot-recommendations.png) |
| HTML report | ![Report](media/screenshot-report.png) |
| Progress | ![Progress](media/screenshot-progress.png) |

## Install (Marketplace / VSIX)

1. Install **CodeStrata** from the VS Code Marketplace (or `Install from VSIX…`).
2. Open a repository folder.
3. On first run, the extension detects **CodeStrata Engine** or offers **Install Engine**.
4. Choose **Run First Engineering Assessment**.

You should not need to read docs first — guided install uses `uv tool`, `pipx`, or
`python -m pip install --user 'codestrata[mcp]'` (official Quick Start family).

## First run

| Engine state | What happens |
| ------------ | ------------ |
| Found & compatible | Offer **Run First Engineering Assessment** |
| Missing | Welcome → **Install Engine** / **Learn More** |
| After install | `codestrata version` + `codestrata doctor`, then assess or optional AI setup |

Optional AI (Bedrock / OpenAI / Azure OpenAI / Anthropic) opens **Engine**
configuration guidance only — **credentials are never stored in the extension**.
Deterministic assessment (`--no-ai`) remains the default.

## Manual Engine install

```bash
python3.12 -m pip install --user 'codestrata[mcp]'
codestrata version
```

Or set `codestrata.engine.executable` to an absolute path.  
Engine docs: [Quick Start](https://docs.codestrata.ai/getting-started/) · [VS Code extension guide](https://docs.codestrata.ai/extensions/vscode).

## Commands

| Command | Purpose |
| ------- | ------- |
| Run Engineering Assessment | Deterministic assess (default) |
| Run Engineering Assessment with AI | Optional Engine AI |
| Install CodeStrata Engine | Guided install |
| Show Welcome / First Run | Replay onboarding |
| Check CodeStrata Environment | Resolve Engine + doctor |
| Initialize CodeStrata Configuration | `codestrata init` |
| Open Engineering Assessment Report | Latest `report.html` |
| Refresh Findings / Recommendations | Reload artifacts |
| Clear CodeStrata Results | Clear trees + diagnostics |
| Open CodeStrata Output | Output channel |
| Open Documentation | Engine Quick Start |

## Settings

| Setting | Purpose |
| ------- | ------- |
| `codestrata.engine.executable` | Explicit CLI path |
| `codestrata.assessment.outputDirectory` | `--output` |
| `codestrata.assessment.configPath` | Optional `codestrata.toml` |
| `codestrata.assessment.defaultNoAi` | Deterministic default |
| `codestrata.assessment.extraArgs` | Advanced passthrough (protected flags stripped) |
| `codestrata.findings.groupBy` | Tree grouping |
| `codestrata.ai.providerHint` | Messaging only |

**Discovery order:** configured → workspace `.venv` → active Python → `PATH`.

## Compatibility

| Contract | Support |
| -------- | ------- |
| VS Code | `^1.85.0` |
| CodeStrata Engine | `>=0.1.0 <2.0.0` |
| Report schema | `1.2` (major `1.x`) |
| Edition | Community Edition |

See also [CONTRIBUTING.md](CONTRIBUTING.md), [EXTRACTION.md](EXTRACTION.md), and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

## Local development

```bash
npm install
npm test
npm run test:host   # Extension Host
npm run package     # Build .vsix (do not publish from this phase)
```

F5: open this folder → **Run CodeStrata Extension**.

## Privacy & security

See [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md). No Platform connection;
no default telemetry; Workspace Trust respected.

## Community scope

Local Engine · local reports · optional AI via Engine providers.  
**Not included:** Platform APIs, Enterprise Edition.

## FAQ

**Q: Assessment failed with a raw process error?**  
Use **Install Engine** or **Check Environment**. The extension surfaces install guidance instead of bare spawn errors when Engine is missing.

**Q: Where do AI keys go?**  
Only in Engine configuration — never extension settings, never Platform keys.

**Q: Can I extract this repo?**  
Yes — see [EXTRACTION.md](EXTRACTION.md) for `codestrata-vscode` standalone readiness.

## Support

[SUPPORT.md](SUPPORT.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · Canonical docs: [docs.codestrata.ai/extensions/vscode](https://docs.codestrata.ai/extensions/vscode)
