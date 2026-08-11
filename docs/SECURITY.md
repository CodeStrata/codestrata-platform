# Security Policy

## Supported projects

This policy covers the **CodeStrata Documentation** portal (`codestrata-docs`)
static site and its build tooling.

Related Community projects (Engine, VS Code) publish their own
`SECURITY.md` files in their repositories.

## Reporting a vulnerability

Please report security issues **privately**. Do not open a public GitHub issue
with exploit details, credentials, or private repository contents, and **do not
disclose publicly** before coordinated release of a fix or advisory.

Include:

- Description of the issue
- Steps to reproduce
- Affected component (docs site, CI, dependency)
- Your contact for follow-up
- Any coordinated disclosure timing preferences

Use the security contact channel published for CodeStrata Community repositories
(GitHub Security Advisories when enabled, or the maintainer contact listed on the
public organization profile — no personal emails are published in this file).

You should receive an acknowledgment within **7 days**.

## Documentation portal baseline

- No authentication
- No credential collection
- No analytics by default
- No secrets in the repository

Community product architecture transparency (API, Data Lake, Insights, reports)
lives on the published docs site:

- https://docs.codestrata.ai/architecture/community-cloud
- https://docs.codestrata.ai/architecture/data-lake
- https://docs.codestrata.ai/architecture/insights
- https://docs.codestrata.ai/security/source-locality
