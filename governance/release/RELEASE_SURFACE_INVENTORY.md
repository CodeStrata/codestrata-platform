# Community Release Surface Inventory

**Authority:** Phase 14.2  
**Machine source:** `python scripts/validate_release.py` → `release-surface-inventory.json`  
**Export boundary:** [`public-export-manifest.yaml`](../../public-export-manifest.yaml) (v2)

## Classification legend

| Class | Meaning |
| --- | --- |
| `public_release` | May be distributed in public Community mirrors / packages |
| `private_release` | Staged destination mirrors that remain private GitHub repositories |
| `internal_only` | Monorepo engineering only |
| `generated` | Build/assessment outputs; never ship as product source |
| `test_only` | Tests / synthetic fixtures |
| `development_only` | Maintainer tooling |
| `secret_sensitive` | Credentials / env secrets |
| `customer_specific` | Customer packs (none shipped in Community) |
| `commercial_platform_only` | Platform commercial runtime |

## Top-level surfaces

| Path | Classification | Notes |
| --- | --- | --- |
| `engine/` | public_release | Community Engine CLI/package |
| `docs/` | private_release | Private codestrata-docs mirror |
| `examples/` | public_release | Showcase manifests / expected results |
| `cursor-plugin/` | private_release | Private codestrata-cursor mirror |
| `vscode-plugin/` | private_release | Private codestrata-vscode mirror |
| `platform/` | commercial_platform_only | Never export |
| `governance/` | internal_only | Never export as product tree |
| `knowledge/` | internal_only | Never export |
| `test-fixtures/` | test_only | sample-js may be allowlisted via `extra_includes` |
| `.codestrata-test-knowledge/` | test_only | Synthetic secrets — never publish |
| `.codestrata-examples/` | development_only | Local clones |
| `.export-staging/` | generated | Staging only |
| `reports/` | generated | Local assessment outputs |
| `scripts/` | development_only | Maintainer scripts |
| `public-export-manifest.yaml` | development_only | Authoritative export allowlist |
| `.env` | secret_sensitive | Forbidden |
| `.env.example` | public_release | Placeholder names only |

## Distributed components

| Component | Source | Destination repo | Visibility | Package form |
| --- | --- | --- | --- | --- |
| codestrata-engine | `engine/` | codestrata-engine | public | PyPI sdist/wheel |
| codestrata-examples | `examples/` | codestrata-examples | public | Source archive |
| codestrata-docs | `docs/` | codestrata-docs | private | Docs site / archive |
| codestrata-cursor | `cursor-plugin/` | codestrata-cursor | private | VSIX / Marketplace |
| codestrata-vscode | `vscode-plugin/` | codestrata-vscode | private | VSIX / Marketplace |

## Explicit exclusions (non-exhaustive)

- Internal Platform implementation and commercial APIs
- Customer-specific rule packs
- Credentials / `.env*` (except `.env.example`)
- Private governance notes and proprietary architecture drafts
- Benchmark machine-personal paths / private hostnames
- Temporary export artifacts outside staging workflow
- Test secrets under `.codestrata-test-knowledge/`
- `.git/`, `.venv/`, caches, `build/`, `dist/`, local `reports/`

**Rule:** Allowlist wins. Absence from a denylist is never sufficient for publication.
