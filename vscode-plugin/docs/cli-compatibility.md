# CLI and extension version compatibility (Slice 13.11)

Policy: `community-vscode-cli-compatibility-policy:1.0`

## Purpose

Decide whether a discovered CodeStrata Engine CLI is supported by this extension.

Discovery answers: *Can I find a CLI?*  
Compatibility answers: *Is this CLI supported?*

## Matrix (extension 0.2.0)

| CLI | Verdict |
| --- | --- |
| `0.2.x` (no prerelease) | `supported` |
| `0.1.x` / older `0.0.x` | `upgrade_cli` |
| `0.3.x+` on major 0 | `downgrade_cli` |
| major ≥ 1 | `unsupported_major` |
| prerelease | `unsupported_prerelease` |
| invalid / missing | `invalid_version` / `unknown_version` |

## Ordering

workspace → repository init → CLI discovery → **CLI compatibility** → AI confirm →
telemetry consent → progress → assessment

Compatibility failure stops the workflow: no assessment, telemetry, analytics,
progress, report, or automatic recovery.

## Doctor

Reuses the compatibility decision from discovery (no second version probe).

Labels: Compatible · Upgrade Required · Unsupported Version · Invalid Version

## Installation guidance

Incompatible results map to Slice 13.3 `install_supported_version` guidance.
No automatic install or download.

## Related

- [cli-discovery.md](./cli-discovery.md)
- [cli-installation.md](./cli-installation.md)
- [telemetry-consent-integration.md](./telemetry-consent-integration.md)
