# Production hardening checklist

Use before a Community release candidate or commercial deployment.

## Defaults

- [ ] Profile `community` (or `local`) — Enterprise KG disabled
- [ ] Assess runs with `--no-ai` unless AI is intentionally required
- [ ] MCP disabled unless explicitly enabled; bind `127.0.0.1`
- [ ] Knowledge store / projection disabled unless needed
- [ ] `token_env` used for GitHub auth (no embedded tokens)

## Runtime bounds

- [ ] `analysis.runtime.max_source_files` appropriate for target repos
- [ ] `analysis.runtime.max_source_chars` / workers reviewed
- [ ] Provider timeouts configured (Bedrock/OpenAI/PMD/git)

## Supply chain

- [ ] `pip-audit` clean for runtime dependencies (ignore or upgrade known dev-only issues)
- [ ] Optional extras reviewed separately (`bedrock`, `openai`, `mcp`, `pgvector`)
- [ ] SBOM refreshed (`engine/docs/security/sbom-cyclonedx.json` when generated;
      mark as an environment snapshot, not a signed release artifact)
- [ ] `python scripts/security_check.py` passes

## Export / Community surface

- [ ] `python scripts/validate-public-exports.py` passes
- [ ] Enterprise KG paths absent from `codestrata-engine` staging
- [ ] `platform/` absent from all public exports
- [ ] Extension hook `codestrata.extensions` present

## Verification

- [ ] `ruff check .`
- [ ] `mypy engine/src`
- [ ] `pytest`
- [ ] Boundary tests: `pytest tests/architecture`
- [ ] Fresh engine export install + assess smoke
