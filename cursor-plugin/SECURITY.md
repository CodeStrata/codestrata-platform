# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.2.x   | Yes       |
| 0.1.x   | Best effort |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities, and
**do not disclose publicly** before coordinated release of a fix or advisory.

Report privately via GitHub Security Advisories on
[codestrata-cursor](https://github.com/sknampally/codestrata-cursor), or via the
security contact listed on the repository profile (no personal emails are
published in this file).

Include a description, reproduction steps, affected versions/commits, and any
coordinated disclosure timing preferences.

You should receive an acknowledgment within **7 days**.

## Scope

- Thin client of **CodeStrata Engine** — no independent source analysis
- No CodeStrata Platform API calls from this Community extension
- Do not store AI provider secrets or Platform API keys in extension settings
- Engine execution and `.cursor/rules` writes require Workspace Trust
