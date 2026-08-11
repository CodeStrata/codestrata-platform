# Clean install and update validation

Policy: `community-vscode-clean-install-policy:1.0`

## Purpose

Validate that the packaged CodeStrata VS Code extension (v0.2.1) can be
installed in an isolated environment, activates cleanly, and supports the
verified Community workflow without developer-machine assumptions.

This is release-readiness validation — not a new product feature.

## Procedure (human / CI)

1. `cd vscode-plugin && npm test && npm run package`
2. Install the produced `codestrata-assessment-0.2.1.vsix` into an **isolated**
   VS Code user-data / extensions directory (never the developer profile).
3. Open a clean workspace folder.
4. Confirm activation does not probe CLI, prompt telemetry, init, or assess.
5. Use **Install CodeStrata Engine** guidance if CLI is missing (no auto-install).
6. With Engine CLI `0.2.x` available: **Initialize Repository** → **Run Assessment**
   → **Open HTML Report**.
7. Confirm telemetry prompt default is Deny; explicit Allow / No Thanks persists
   and can be changed via **Telemetry Settings**.
8. Update over a prior package (or synthetic prior fixture) and confirm command
   IDs / stable settings remain.

## Isolated test assumptions

- Temporary `user-data-dir` and extension home
- Controlled PATH / CLI candidates
- No live AI providers
- No Marketplace publish
- No production telemetry

## State preservation

| State | Clean install | Update | Notes |
| --- | --- | --- | --- |
| Onboarding (`firstRunCompleted` / `welcomeDismissed`) | May persist | Product-owned | Not telemetry consent |
| Telemetry preference | Undecided until explicit Allow / No Thanks; then persisted in extension `globalState` | Survives update when present | Change via Telemetry Settings |
| Installation / machine identity | Forbidden | Forbidden | Not used |
| `codestrata.engine.executable` | User-owned | Survives update | Explicit setting |

## Cursor absence

Clean install/update must not reintroduce Cursor packages, IDs, commands,
settings, or Marketplace assets.

## Limitations

- Full Extension Host UI automation may be unavailable in some environments
- Update may use a synthetic prior package when no historical VSIX exists
- One-OS execution with static cross-platform coverage
- Marketplace publication is a separate human-approved step

## Epic completion

Epic 13 completion verification is provided by
`verification/vscode_epic13_completion/`
(`vscode-epic13-completion-verification:1.0.0`). Marketplace publication,
release tagging, and production deployment remain separate release gates.

## Related

- [marketplace-documentation.md](./marketplace-documentation.md)
- [MARKETPLACE.md](../MARKETPLACE.md)
- [cli-compatibility.md](./cli-compatibility.md)
- [cli-installation.md](./cli-installation.md)
