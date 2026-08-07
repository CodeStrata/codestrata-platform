# Source locality (Slice 13.10)

Policy: `community-vscode-source-locality-policy:1.0`

## Purpose

Precisely state what the VS Code Community extension does and does not do with
repository source, reports, configuration, telemetry, analytics, and AI.

This is not a marketing claim. It separates:

1. **Extension behavior**
2. **Engine CLI local assessment**
3. **Engine AI-provider flow** when an external provider is configured

## Extension guarantees

- Does not upload, archive, or package repository source
- Does not upload report contents, findings, or evidence
- Has no Community Cloud or Data Lake runtime client
- Has no direct AI-provider SDK client
- Does not own or read provider API keys
- Does not mutate source files or Git
- Telemetry/analytics exclude source, paths, report content, and identities
- Telemetry transport and analytics sink remain unavailable

## Standard assessment

```text
VS Code extension → local child process → Engine CLI
  → local repository assessment → local generated artifacts
  → optional local report open
```

From the extension’s perspective, standard assessment is local-only.

## AI-enabled assessment

```text
VS Code extension → local Engine CLI (--with-ai)
  → Engine assessment
  → Engine AI-provider integration (when configured)
  → local report/artifacts
```

The VS Code extension does not upload repository source. AI-enabled assessment
is executed by the local CodeStrata Engine; when an external AI provider is
configured, the Engine may send provider request content according to the
configured AI-provider data flow.

## Approved Engine-owned local artifacts

- `codestrata.toml` (config)
- `report.json` / `report.html` (and related run artifacts)

Written by the Engine CLI, not by extension filesystem writes.

## Navigation vs transmission

`vscode.env.openExternal` may open:

- a fixed trusted documentation URL (user-triggered), or
- a validated local `file:` HTML report URI

Neither transmits repository source.

## Deferred

~~CLI compatibility matrix — Slice **13.11**~~ — [cli-compatibility.md](./cli-compatibility.md).  
~~Marketplace branding — Slice **13.12**~~ — [marketplace-branding.md](./marketplace-branding.md). ~~Marketplace documentation — Slice **13.13**~~ — [marketplace-documentation.md](./marketplace-documentation.md). Clean install validation — Slice **13.14**.

## Related

- [assessment-execution.md](./assessment-execution.md)
- [telemetry-consent-integration.md](./telemetry-consent-integration.md)
- [html-report-opening.md](./html-report-opening.md)
- [PRIVACY.md](../PRIVACY.md)
