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
[codestrata-vscode](https://github.com/sknampally/codestrata-vscode), or via the
security contact listed on the repository profile (no personal emails are
published in this file).

Include a description, reproduction steps, affected versions/commits, and any
coordinated disclosure timing preferences.

You should receive an acknowledgment within **7 days**.

## Scope notes

- This extension is a **thin client** of **CodeStrata Engine**. It does not send
  repository source code to CodeStrata Platform or third parties on its own.
- Assessments run locally through the Engine CLI.
- Do not place AI provider secrets or Platform API keys in extension settings.
- Engine execution respects VS Code Workspace Trust.
