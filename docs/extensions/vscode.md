---
title: CodeStrata VS Code Extension
description: Run Engineering Assessments from VS Code with CodeStrata Engine discovery, findings, and reports.
---

# CodeStrata VS Code Extension

Run local **Engineering Assessments** without leaving VS Code.

## Purpose

Bring Engine CLI assessments into the editor: progress, findings explorer,
recommendations, diagnostics, and HTML report access.

## Installation

1. Install **[CodeStrata for VS Code](https://marketplace.visualstudio.com/items?itemName=CodeStrataAI.codestrata-assessment)**
   from Visual Studio Marketplace (`CodeStrataAI.codestrata-assessment`).
   Extension source is private; the listing is the public distribution channel.
2. Open a repository folder.
3. On first run, the extension detects **CodeStrata Engine** or offers guided install.
4. Optionally run **Initialize Repository** (Engine writes
   `codestrata.toml`; already-initialized is preserved; invalid/partial config
   fails closed). See the extension repository docs for initialization boundaries.
5. Run your first assessment, then open the generated report when prompted.

The extension follows CodeStrata Design System identity on native VS Code surfaces
(no website CSS in the editor chrome). Marketplace gallery assets are separate.

Manual Engine install if needed:

```bash
python3.12 -m pip install --user 'codestrata[mcp]'
codestrata version
```

## Engine dependency

The extension requires CodeStrata Engine. It does not analyze source independently.

## Automatic Engine discovery

Resolution order typically:

1. Configured executable (`codestrata.engine.executable`)
2. Workspace `.venv`
3. Active Python environment
4. `PATH`

Guided install uses supported mechanisms (`uv tool`, `pipx`, or `pip --user`).

## First assessment

Use **Run Assessment** (deterministic / `--no-ai` by default).

When Engine consent is undecided, the extension shows a native prompt
(semantically equivalent to the CLI):

- **Allow** — persists **v2** Yes (usage metrics + privacy-safe assessment insights)
- **No Thanks** — persists Disabled (no Community collection)
- **Learn More** — opens privacy docs; does **not** enable telemetry

CLI and VS Code share the same Engine-owned consent preference. After an
explicit choice, the prompt is not repeated for that preference. Change later
via **CodeStrata: Telemetry Settings** or `codestrata telemetry enable|disable`.
Assessment continues whether you allow or decline.
## Findings, recommendations, diagnostics, reports

After a successful assessment the extension loads public artifacts into:

- Findings tree
- Recommendations view
- Editor diagnostics
- Open HTML report command (opens `.codestrata-artifacts/assessments/<repository-id>/current/assessment.html`)

## Publish / share current report

**Publish/Share Current Report** is an **explicit** action. Assessment never
auto-publishes. The command:

1. Shows one public-sharing confirmation (includes private/local warning when
   the repository id looks like `local-*`)
2. Invokes Engine `codestrata report publish --confirm-public-publish`
   (adds `--acknowledge-private-repository` when needed)
3. Shows the branded URL (`https://reports.codestrata.ai/r/…`) for copy/open

Publishing does **not** enable telemetry and does not require a temporary
telemetry environment variable. Local HTML/JSON reports remain authoritative on
disk. No AWS account or Secrets Manager access is required.

## Optional AI

**Run Engineering Assessment with AI** uses Engine provider configuration
(`[ai].provider` / environment credentials). Credentials are **not** stored in
the extension. There is **no** separate VS Code provider-selection control panel
in the current Community candidate surface — AI support is through the Engine.

Default assessment remains local/deterministic unless an AI-enhanced Engine path
is explicitly chosen. See [AI Providers](/ai-providers/) and
[Source Locality](/security/source-locality).

## Privacy and security

- Local Engine execution
- No Platform requirement for Community assessment
- Telemetry default is **not configured / disabled** until the user chooses;
  eligible assessment commands may prompt (default Deny). Explicit Allow or
  No Thanks is persisted through the **Engine** (shared with CLI) and can be
  changed via Telemetry Settings or CLI `telemetry enable|disable`
- Community Cloud authority: `https://api.codestrata.ai`
- See [Privacy](/security/privacy), [Source Locality](/security/source-locality),
  [AI Providers](/ai-providers/), [Telemetry](/reference/telemetry),
  [Data Collection](/security/data-collection),
  [Retention and Deletion](/security/retention-and-deletion),
  [Security](/security/), and [Community Cloud API](/reference/community-api/)
- Telemetry opt-out / deny does **not** revoke an already published public
  report; revoke is a separate authenticated API action
- Local reports under `.codestrata-artifacts/` remain user-controlled

## Detailed reference

Packaging and Marketplace listing:
[CodeStrata for VS Code](https://marketplace.visualstudio.com/items?itemName=CodeStrataAI.codestrata-assessment)
(`CodeStrataAI.codestrata-assessment`).
Extension source is not a Community public GitHub repository.
