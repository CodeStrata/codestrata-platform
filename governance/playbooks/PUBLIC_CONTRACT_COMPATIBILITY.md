# Public Contract Compatibility Policy

**Status:** Normative  
**Authority:** Playbook (public SDK / API / CLI / MCP / report compatibility)  
**Audience:** Maintainers, SDK authors, extension authors, integrators

This playbook is the **detailed compatibility authority** for how CodeStrata
evolves **externally consumable** contracts. Related standards (for example
[`API_STANDARDS.md`](../standards/API_STANDARDS.md)) must defer to this document
for versioning, deprecation, and the frozen error envelope rather than
duplicating those rules.

It does not publish language SDKs to registries; it defines the rules those SDKs
must follow.

Canonical product names and Design System:
[`../assets/DESIGN-SYSTEM.md`](../assets/DESIGN-SYSTEM.md).  
Community vs Platform:
[`../constitution/006_COMMUNITY_PLATFORM_BOUNDARIES.md`](../constitution/006_COMMUNITY_PLATFORM_BOUNDARIES.md).

## Surfaces in scope

| Surface | Product | Contract home |
| ------- | ------- | ------------- |
| Platform REST `/api/v1` + OpenAPI | Platform | This playbook + [API_STANDARDS.md](../standards/API_STANDARDS.md) |
| MCP tools / envelopes | Engine + Platform extensions | Engine MCP docs; tool names stable |
| CLI commands / exit codes / `--json*` | Engine | [engine/docs/cli-reference.md](../../engine/docs/cli-reference.md) |
| `codestrata.toml` + profiles | Engine | [engine/docs/configuration-profiles.md](../../engine/docs/configuration-profiles.md) |
| `report.json` (+ companion JSON) | Engine | Schema 1.2 + [REPORT_STANDARDS.md](../standards/REPORT_STANDARDS.md) |
| Public Python package import surface | Engine | Documented modules only (see SDK readiness) |

Out of scope as public contracts: Domain internals, persistence schemas,
unexported private helpers, placeholder extension repos until implemented.

## 1. API versioning (Platform REST)

1. URL prefix carries the major version: `/api/v1`.
2. OpenAPI `info.version` matches the major path segment (`v1`).
3. **Breaking** changes require `/api/v2` (new major) — never silently break v1.
4. **Additive** changes within v1 are allowed: new optional fields, new endpoints,
   new enum values that clients must tolerate unknown.
5. Removing or renaming fields, changing types, or changing auth schemes in a
   non-compatible way is **breaking**.
6. Feature-flagged capabilities may return application errors when disabled;
   OpenAPI may still document them. Clients must handle `4xx`/`503`-class errors.

### Error envelope (frozen)

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {},
    "correlation_id": "string"
  }
}
```

- HTTP status conveys class (401 auth, 404 missing, 409 conflict, 422 validation, …).
- `code` is stable for programmatic handling; `message` is human-oriented and sanitized.
- `details` is optional structured data (for example bounded validation errors).
- `correlation_id` is optional for clients but populated by current servers; also
  echoed in `X-Correlation-Id` / `X-Request-Id` response headers.
- Do not parse free-text `message` for control flow.
- Do not invent alternate envelopes outside `ErrorResponseDto`.

### Authentication

- Production: `Authorization: Bearer <CODESTRATA_PLATFORM_API_KEY>`.
- Shared secret is intentional for current Platform API auth — not OAuth/OIDC.
- Not interchangeable with Engine AI provider credentials.

## 2. JSON report versioning (Engine)

1. Customer `report.json` schema version is **1.2**
   (`schemas/assessment/codestrata.io/v1.2/AssessmentReport.json`).
2. Evolution is **additive** within a schema version (new optional fields/sections).
3. Breaking report shape requires a new schema version directory and dual-read
   guidance before dropping the old version.
4. `manifest.schema_version`, `manifest.contract_version`, and related manifest
   fields are part of the public contract.
5. Compare runs with `volatile_fields` / structural equality helpers — do not
   treat timestamps as stable.

## 3. CLI compatibility (Engine)

1. Primary command names (`assess`, `init`, `doctor`, `version`, `config`, `mcp`,
   `examples`, `report`, …) are public.
2. Prefer additive options. Removing a flag requires a deprecation window.
3. Exit codes: `0` success, `1` operational/config failure, `2` usage/hard error.
4. Machine-readable outputs (`--json-summary`, `config …` JSON modes, `examples --json`)
   must remain parseable; additive keys allowed.
5. `codestrata scan` remains legacy/advanced; new automation should use `assess`.

## 4. Configuration compatibility

1. Unknown TOML keys should fail closed or warn per settings validation — do not
   silently ignore security-sensitive keys.
2. Profile defaults may change only when security-preserving; document in release notes.
3. Precedence remains: CLI > environment > TOML > profile defaults.
4. Deprecate settings with release notes + `config validate` guidance before removal.
5. Secrets never belong in TOML (store env var *names* only).

## 5. MCP compatibility

1. Tool **names** are the wire contract (underscores). Dotted aliases are optional.
2. Community tool set and Platform extension set differ by install — clients must
   discover tools at runtime (`codestrata mcp tools` / MCP `list_tools`).
3. Envelope fields for repository-intelligence tools evolve additively.
4. Do not rename `enterprise_*` tools solely for branding; document product name
   separately (Engineering Knowledge Graph).

## 6. SDK compatibility expectations

1. Generated clients should target OpenAPI for Platform and documented CLI/MCP/report
   contracts for Engine.
2. SDKs must tolerate unknown JSON properties (forward compatibility).
3. Pin major API version (`v1`) in client base paths.
4. Do not publish SDKs that require private monorepo imports.

## 7. Deprecation policy

| Stage | Action |
| ----- | ------ |
| Announce | Release notes + docs mark deprecated; still works |
| Warn | Prefer CLI/config/runtime warnings when practical |
| Remove | Only after at least one minor release with announce, or with major version bump for REST |

Support window for a deprecated Community Engine CLI flag or config key:
**minimum one minor release** after announcement unless a security issue requires
immediate removal.

## 8. Ready-for-public-SDK checklist

- [x] Versioning + deprecation policy published (this playbook)
- [x] Error envelope documented and exposed in OpenAPI components
- [x] Integration examples for REST / MCP / CLI / report JSON
- [x] Community vs Platform MCP capability matrix documented
- [x] Extension readiness gaps documented (placeholders; APIs identified)
- [x] Remaining non-blocking recommendations recorded in SDK readiness

**Sign-off:** These contracts are the public baseline for extension and customer
integrations. Publishing language SDKs to package registries remains a later
release decision.

## References

- [API_STANDARDS.md](../standards/API_STANDARDS.md)
- [REPORT_STANDARDS.md](../standards/REPORT_STANDARDS.md)
- [SDK_READINESS.md](../../platform/docs/product-experience/SDK_READINESS.md)
- [EXTENSION_READINESS.md](../../platform/docs/product-experience/EXTENSION_READINESS.md)
- [INTEGRATION_EXAMPLES.md](../../platform/docs/product-experience/INTEGRATION_EXAMPLES.md)
