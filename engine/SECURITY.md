# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes |

Older pre-release branches are unsupported unless noted in a GitHub Security
Advisory.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report privately by emailing the maintainer listed in the repository profile, or
by opening a private GitHub Security Advisory if enabled on the repository.

Include:

* A description of the issue and its impact
* Steps to reproduce (proof of concept if available)
* Affected versions or commit SHAs if known

You should receive an acknowledgment within **7 days**. We aim to provide a fix
or mitigation timeline within **30 days** for confirmed issues in supported
versions, then coordinate disclosure with you.

## Scope notes for CodeStrata

* Never commit secrets, tokens, or `.env` files.
* Configuration should reference credentials via environment variable names
  (`token_env`), not embed secret values.
* Reports and JSON artifacts must not include runtime credentials or absolute
  host paths that expose private environments.
* Community Edition **never executes** analyzed repository code and does not
  import target modules.
* External AI providers and Enterprise KG are **disabled by default**.

## Related documentation

* [Threat model](docs/security/threat-model.md)
* [Security architecture](docs/security/architecture.md)
* [Production hardening checklist](docs/security/production-hardening-checklist.md)
* [MCP security](docs/mcp/security.md)
