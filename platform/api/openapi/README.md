# Platform API OpenAPI — Internal Engineering Guide

**Audience:** Internal Platform engineers only.  
**Hostname:** `https://platform.codestrata.ai`  
**Docs (internal):** `https://platform.codestrata.ai/api/docs`  
**Canonical contract:** [`openapi.yaml`](openapi.yaml)

This tree is **not** Community documentation. It must never appear in
`codestrata-docs`, public sitemaps, or codestrata.ai navigation.

## Principles

1. **OpenAPI 3.1 is the source of truth** for Platform HTTP contracts.
2. **Swagger UI is a projection** generated from OpenAPI — never edit Swagger as
   the contract.
3. Document only implemented routes, approved architecture, or explicitly
   **PROPOSED** future contracts (`x-codestrata-status: proposed`).
4. Reuse Community schemas (e.g. Assessment Report 1.2) by reference — do not
   duplicate them inside Platform components.
5. Visual design reuses the CodeStrata design system (same tokens as Community
   docs / codestrata.ai).

## Layout

```text
platform/api/openapi/
  openapi.yaml          # bundled canonical spec
  openapi.json          # JSON twin for tooling
  inventory.json        # operation counts by status/tag
  paths/                # modular path fragments (by tag)
  schemas/              # per-schema YAML fragments
  responses/            # shared responses
  parameters/           # shared parameters
  examples/             # shared examples
  swagger/              # branded Swagger UI (projection)
  scripts/
    generate_openapi.py # regenerate from live FastAPI app
    check_token_drift.py
  README.md             # this file
  VISUAL_ALIGNMENT.md
```

## Maturity extensions

Every operation MUST declare:

| Extension | Values |
| --------- | ------ |
| `x-codestrata-status` | `implemented` · `partial` · `proposed` · `deprecated` · `internal` |
| `x-codestrata-owner` | owning team / component id |
| `x-codestrata-audience` | `internal` |

`UNKNOWN` is forbidden. `partial` means wired but weakly typed OpenAPI responses.

## How to add an endpoint

1. Implement thin controller + DTO + application service (Platform package only).
2. Ensure OpenAPI tag, summary, request/response models, and status codes are set.
3. Regenerate the canonical spec:

```bash
python platform/api/openapi/scripts/generate_openapi.py
```

4. Mark `partial` ops in `PARTIAL_OPS` inside `generate_openapi.py` when responses
   are still untyped.
5. Run contract tests:

```bash
pytest platform/tests/api/test_contract_openapi.py platform/tests/api/test_openapi.py -q
```

6. Preview Swagger locally (non-production):

```bash
export CODESTRATA_PLATFORM_INTERNAL_API_DOCS=1
uvicorn codestrata_platform.api.app:create_app --factory --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000/api/docs
```

## How to update schemas

- Prefer Pydantic DTOs under `platform/src/codestrata_platform/api/**`.
- Shared envelopes live in `api/dto/common.py` (`ErrorResponseDto`, pagination).
- After DTO changes, regenerate OpenAPI.
- For Community reuse (reports/assessments), link the Engine schema path in
  `x-codestrata-contract.community_schema_reuse` — do not copy JSON Schema bodies.

## Versioning

| Topic | Policy |
| ----- | ------ |
| URL version | `/api/v1` (current reality) |
| Breaking change | New major path `/api/v2` — do not rewrite v1 silently |
| Within major | Additive fields/operations only |
| Deprecation | Document in release notes; keep ≥ one minor cycle |
| OpenAPI version | 3.1.0 |
| API version (`info.version`) | `v1` |

## Authentication

**Implemented:** HTTP Bearer shared secret (`CODESTRATA_PLATFORM_API_KEY`) —
scheme `PlatformApiKey`.

**Proposed (not runtime):** JWT (`PlatformJwt`), OIDC SSO (`PlatformOidc`),
internal service identity.

Never commit secrets. Never confuse Platform API keys with Engine AI provider keys.

## Access control for `/api/docs`

| Environment | Behavior |
| ----------- | -------- |
| `CODESTRATA_PLATFORM_ENV=production\|prod` | Docs mounts disabled |
| Development (default) | Docs enabled when `CODESTRATA_PLATFORM_INTERNAL_API_DOCS=1` (default) |
| Future | Platform auth / SSO / VPN in front of `platform.codestrata.ai` |

Do **not** rely on obscurity, robots.txt, or missing nav links as the only control.
`robots.txt` + `noindex` are defense-in-depth only.

Until production auth for the docs portal exists, treat Swagger as **local-only**.

## Design system / tokens

```bash
cp docs/public/design-tokens/tokens.css \
   platform/api/openapi/swagger/design-tokens/tokens.css
python platform/api/openapi/scripts/check_token_drift.py
```

Fonts: Space Grotesk, Inter, IBM Plex Mono (mirrored under `swagger/fonts/`).

## Public export

`platform/` is never a Community export `source_root`. See
`public-export-manifest.yaml` `never_export_source_roots` and forbid rules.
This OpenAPI tree must stay out of `docs/` and `codestrata-docs`.

## Related

- ADR: [`../../../governance/adr/ADR-001-platform-openapi-source-of-truth.md`](../../../governance/adr/ADR-001-platform-openapi-source-of-truth.md)
- Visual: [`VISUAL_ALIGNMENT.md`](VISUAL_ALIGNMENT.md)
- Audit report: `governance/reports/PLATFORM_API_CONTRACT_FOUNDATION.md`
- API standards: `governance/standards/API_STANDARDS.md`
