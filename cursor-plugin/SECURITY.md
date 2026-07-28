# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.2.x   | Yes       |
| 0.1.x   | Best effort |

## Reporting a vulnerability

Report privately via GitHub Security Advisories on
[codestrata-cursor](https://github.com/sknampally/codestrata-cursor).

## Scope

- Thin client of **CodeStrata Engine** — no independent source analysis
- No CodeStrata Platform API calls from this Community extension
- Do not store AI provider secrets or Platform API keys in extension settings
- Engine execution and `.cursor/rules` writes require Workspace Trust
