# API Standards

**Status:** Normative (updated Phase 9.7)  
**Authority:** Standards

## Objective

Standardize REST/OpenAPI and related transport contracts for CodeStrata Platform
(and any Engine HTTP surfaces if introduced later).

## Scope

Platform REST API under `platform/src/codestrata_platform/api/`.  
Out of scope: inventing new endpoints in Governance phases.

Compatibility and deprecation:
[`../playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md`](../playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md).

## 1. Transport principles

1. Controllers are thin adapters over Application Services.
2. No Domain or persistence types in request/response DTOs.
3. Stable `/api/v1` versioning until a deliberate v2.
4. Additive evolution within a major version; clients must ignore unknown fields.

## 2. OpenAPI expectations

| Field | Expectation |
| ----- | ----------- |
| `info.title` | **CodeStrata Platform API** |
| `info.version` | Major API version (`v1`) |
| Tags | Complete set matching routers |
| Summaries | Verb + resource; product terminology |
| Errors | `ErrorResponseDto` envelope; sanitized messages |
| Security | `PlatformApiKey` Bearer scheme documented |
| Examples | Golden-path request examples for SDK generation |

## 3. Error envelope (frozen)

```json
{"error":{"code":"string","message":"string","details":{}}}
```

See the compatibility playbook for status-code mapping and client rules.

## 4. Naming

- Path segments: kebab-case resources (`knowledge-graphs`, `executive-intelligence`).
- IDs: opaque string identifiers in paths.
- Prefer canonical terms from Product Principles / Naming Conventions.

## 5. Auth & docs exposure

- Production requires API key configuration (`CODESTRATA_PLATFORM_API_KEY`).
- Public probes: `/health`, `/ready` only (as implemented).
- OpenAPI docs may be public outside production when a key is configured.

## 6. References

- [platform/src/codestrata_platform/api/app.py](../../platform/src/codestrata_platform/api/app.py)
- [003_ARCHITECTURE_PRINCIPLES.md](../constitution/003_ARCHITECTURE_PRINCIPLES.md)
- [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md)
- [SDK_READINESS.md](../../platform/docs/product-experience/SDK_READINESS.md)
