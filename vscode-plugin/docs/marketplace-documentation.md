# Marketplace documentation

Policy: `community-vscode-marketplace-documentation-policy:1.0`

## Authority decision

| Document | Role |
| --- | --- |
| [`README.md`](../README.md) | **Authoritative Marketplace-facing listing** |
| [`MARKETPLACE.md`](../MARKETPLACE.md) | Publishing / packaging checklist only |
| [`marketplace-branding.md`](./marketplace-branding.md) | Visual metadata / assets (branding policy 1.0) |

Do not maintain divergent product claims in `MARKETPLACE.md`.

## Purpose

Finalize public Marketplace narrative for extension **0.2.1** so visitors can
understand product purpose, requirements, workflow, privacy, AI qualification,
CLI compatibility, limitations, and support—aligned with verified Community
extension behavior.

## Naming (preserved from branding)

- displayName: **CodeStrata – Engineering Assessment**
- Tagline: **Engineering decisions grounded in code.**
- Version: **0.2.1** (Community Engine/CLI remains **0.2.0**)
- Supported editor: **VS Code** only

## Claim posture (summary)

| Topic | Posture |
| --- | --- |
| Standard assessment | Local Engine CLI |
| AI assessment | Optional; Engine-owned provider flow |
| CLI install | Guidance only — no automatic install |
| Compatibility | Extension 0.2.1 → CLI `0.2.x` |
| Telemetry | Optional; default undecided/disabled; explicit choice persisted locally; Deny default on prompt |
| Source locality | Extension does not upload source to Community services; AI qualified separately |
| Cloud / Data Lake / dashboards | Not claimed (no runtime clients) |
| Cursor | Absent from Marketplace listing |

## Required README sections

See `MARKETPLACE_README_REQUIRED_HEADINGS` in
`src/marketplaceDocs/policy.ts`.

## Deferred

- ~~Clean install / update validation~~ — [clean-install-update.md](./clean-install-update.md)
- Broader documentation-site redesign (future design work)

## Related

- [cli-installation.md](./cli-installation.md)
- [cli-compatibility.md](./cli-compatibility.md)
- [source-locality.md](./source-locality.md)
- [telemetry-consent-integration.md](./telemetry-consent-integration.md)
- [PRIVACY.md](../PRIVACY.md) · [SECURITY.md](../SECURITY.md)
