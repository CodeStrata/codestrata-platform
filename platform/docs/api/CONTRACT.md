# Platform API Contract

**Status:** Phase 14.4  
**API major:** `v1`  
**Audience:** Internal Platform clients

## Version policy

Platform REST contracts are versioned by URL major (`/api/v1`). Additive,
backward-compatible fields may appear within a major. Breaking changes require
a new major path and updated clients.

Responses include header:

```http
X-CodeStrata-API-Version: v1
```

## Error model

All failures use:

```json
{
  "error": {
    "code": "not_found",
    "message": "…",
    "details": null,
    "correlation_id": "…"
  }
}
```

`correlation_id` is optional in older clients but always populated by current
servers. Headers `X-Request-Id` and `X-Correlation-Id` are also set.

## DTO rules

- Public Platform operations use explicit Pydantic request/response DTOs
- No raw `dict` / `Any` response contracts for business routes
- Incoming requests are validated by FastAPI/Pydantic (HTTP 422)
- Outgoing aggregation responses are validated before return

## Inventory

Machine inventory (gitignored):

- `.generated/platform-contract-inventory.json`

Regenerate:

```bash
python platform/scripts/generate_contract_inventory.py
python platform/api/openapi/scripts/generate_openapi.py
```

## OpenAPI

Canonical OpenAPI lives under `platform/api/openapi/` (internal docs UI at
`/api/docs` when enabled).

## Related

- Compatibility authority: `governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md`
- API standards: `governance/standards/API_STANDARDS.md`
- Error DTO: `codestrata_platform.api.dto.common.ErrorResponseDto`
