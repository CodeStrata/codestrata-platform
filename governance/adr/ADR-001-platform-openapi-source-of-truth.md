# ADR-001: Platform OpenAPI as Source of Truth (Internal)

**Status:** Accepted  
**Date:** 2026-07-28  
**Phase:** 12.4  
**Audience:** Internal Platform engineers

## Context

CodeStrata Platform exposes a large FastAPI surface (`/api/v1`). Engineers need a
stable contract before customer-facing API publication. Community documentation
must not absorb Platform API details.

## Decision

1. **OpenAPI 3.1** under `platform/api/openapi/` is the **canonical** Platform
   HTTP contract.
2. **Swagger UI** at `/api/docs` is a **generated projection**, not the source
   of truth.
3. The internal hostname is **`https://platform.codestrata.ai`** with docs at
   **`/api/docs`** and machine contracts at `/api/openapi.yaml` and
   `/api/openapi.json`.
4. Every operation declares `x-codestrata-status`, `x-codestrata-owner`, and
   `x-codestrata-audience`.
5. **Versioning** remains `/api/v1`; breaking changes require `/api/v2` — do not
   silently rewrite existing routes.
6. **Contract tests** fail on drift between live FastAPI routes and the
   checked-in OpenAPI.
7. **Design system reuse:** Platform Swagger uses the same tokens, fonts, and
   theme behavior as Community docs / codestrata.ai.
8. **Public exclusion:** this tree is never exported to Community repositories
   or `codestrata-docs`, never linked from codestrata.ai, and is `noindex`.

## Access control

Production disables the docs mounts. Development may serve them locally.
Future production exposure of `platform.codestrata.ai/api/docs` MUST sit behind
Platform authentication, SSO, and/or VPN — not obscurity alone.

## Consequences

- Controllers/DTOs still drive initial generation via
  `scripts/generate_openapi.py`; long-term codegen may reverse (OpenAPI → stubs).
- Community Engine and Engineering Intelligence remain untouched.
- Proposed auth (JWT/OIDC) and RFC 9457 Problem Details are documented as
  **proposed** without inventing runtime endpoints.

## References

- `platform/api/openapi/README.md`
- `governance/standards/API_STANDARDS.md`
- `governance/reports/PLATFORM_API_CONTRACT_FOUNDATION.md`
