# 005 — Security & Privacy Principles

**Status:** Foundation  
**Authority:** Constitution

## Objective

State non-negotiable security and privacy principles for CodeStrata Engine and
CodeStrata Platform.

## Scope

Principles and pointers. Detailed threat models and hardening checklists remain
in existing security docs.

## 1. Principles

1. **No credential or secret leakage** in logs, errors, OpenAPI examples, or reports.
2. **Sanitize diagnostics** — never return raw provider or database errors to clients.
3. **Tenant isolation** — cross-tenant access must fail closed (404/deny, not leak).
4. **Least privilege** for cloud providers and API keys.
5. **Source retention policy** — do not retain customer source beyond designed
   artifact / workspace policies.
6. **Production auth is required** for Platform commercial APIs.

## 2. Data classes (outline)

| Class | Examples | Handling |
| ----- | -------- | -------- |
| Secrets | API keys, tokens, DSN passwords | Never log; redact |
| Customer source | Repo files, excerpts | Scoped workspace / artifacts only |
| Assessment artifacts | report.json, HTML, evidence | Tenant-scoped storage |
| Telemetry / diagnostics | Correlation IDs, failure categories | Sanitized |

<!-- TODO: Formalize data classification and retention periods. -->

## 3. Engineering controls (pointers)

- Threat model: [engine/docs/security/threat-model.md](../../engine/docs/security/threat-model.md)
- Hardening checklist: [engine/docs/security/production-hardening-checklist.md](../../engine/docs/security/production-hardening-checklist.md)
- Release security gate: `scripts/security_check.py` via `verify_release`

## 4. Privacy commitments (outline)

<!-- TODO: Author customer-facing privacy commitments for commercial Platform. -->

## 5. References

- [002_ENGINEERING_CONSTITUTION.md](002_ENGINEERING_CONSTITUTION.md)
- [engine/docs/security/README.md](../../engine/docs/security/README.md)
