# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.2.x   | Yes       |
| 0.1.x   | Best effort |

## Reporting a vulnerability

Please report security issues privately via GitHub Security Advisories on
[codestrata-vscode](https://github.com/sknampally/codestrata-vscode) or contact the
maintainers. Do not open a public issue for credential or exploit reports.

## Scope notes

- This extension is a **thin client** of **CodeStrata Engine**. It does not send
  repository source code to CodeStrata Platform or third parties on its own.
- Assessments run locally through the Engine CLI.
- Do not place AI provider secrets or Platform API keys in extension settings.
- Engine execution respects VS Code Workspace Trust.
