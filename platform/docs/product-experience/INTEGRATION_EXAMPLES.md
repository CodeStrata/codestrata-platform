# Integration examples (Phase 9.7)

Production-oriented snippets for future SDK and extension authors. Placeholders
only — never commit secrets.

Compatibility:
[PUBLIC_CONTRACT_COMPATIBILITY.md](../../../governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md).

## CLI (Community Engine)

```bash
python -m pip install 'codestrata[mcp]'
codestrata init
codestrata doctor
codestrata assess --repo . --output reports --no-ai --quiet --json-summary
```

Parse `--json-summary` from stdout for scripting. Open HTML:

```bash
REPORT_DIR=$(ls -dt reports/*/* | head -1)
test -f "$REPORT_DIR/report.html"
```

Validate JSON contract:

```bash
codestrata report validate "$REPORT_DIR/report.json" --json
```

## JSON report consumption

```python
import json
from pathlib import Path

report = json.loads(Path("reports/.../report.json").read_text(encoding="utf-8"))
manifest = report["manifest"]
assert manifest["schema_version"]  # public: 1.2 family
findings = report["assessment"].get("findings") or []
# Tolerate unknown keys — additive evolution within schema version
```

Schema:
`engine/src/codestrata/resources/schemas/assessment/codestrata.io/v1.2/AssessmentReport.json`.

## MCP (Community)

```json
{
  "name": "run_assessment",
  "arguments": {"repository": ".", "with_ai": false}
}
```

```json
{
  "name": "list_findings",
  "arguments": {"run_id": "<assessment-run-id>", "limit": 50}
}
```

Enable `[mcp].enabled = true`. Catalog: [engine/docs/mcp/tools.md](../../../engine/docs/mcp/tools.md).

## MCP (Platform extensions)

```json
{
  "name": "repository_search",
  "arguments": {
    "query": "authentication",
    "tenant_id": "example-tenant",
    "repository_id": "example-repo",
    "top_k": 5
  }
}
```

Discover tools at runtime — Community-only installs lack `repository_*`.

## Platform REST

```bash
export CODESTRATA_PLATFORM_API_KEY=...   # not an AI provider token
export PLATFORM_BASE=https://platform.example

curl -sS -X POST "$PLATFORM_BASE/api/v1/organizations" \
  -H "Authorization: Bearer $CODESTRATA_PLATFORM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme Engineering"}'
```

```bash
curl -sS -X POST "$PLATFORM_BASE/api/v1/answers" \
  -H "Authorization: Bearer $CODESTRATA_PLATFORM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the highest severity findings?",
    "organization_id": "org_...",
    "workspace_id": "ws_...",
    "repository_id": "repo_..."
  }'
```

Error shape:

```json
{"error":{"code":"unauthorized","message":"...","details":null}}
```

OpenAPI: `GET $PLATFORM_BASE/openapi.json`.

## OpenAPI-driven SDK sketch

1. Fetch `/openapi.json`.
2. Generate client for `/api/v1` only.
3. Inject Bearer token from `CODESTRATA_PLATFORM_API_KEY`.
4. Map `ErrorResponseDto` to typed exceptions by `error.code`.
5. Ignore unknown response properties.

## Related

- [SDK_READINESS.md](SDK_READINESS.md)
- [EXTENSION_READINESS.md](EXTENSION_READINESS.md)
- [API_MCP_EXPERIENCE.md](API_MCP_EXPERIENCE.md)
- [engine/docs/examples.md](../../../engine/docs/examples.md)
