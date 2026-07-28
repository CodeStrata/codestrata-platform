# CLI Audit

> **ARCHIVE CANDIDATE (Phase 12.2.2)** — Retained for history. Do not treat as current public documentation. Prefer CHANGELOG / governance reports / public `docs/` for current guidance. File was **not deleted**.


**Phase:** 9.1 audit  
**Source:** `codestrata --help` (2026-07-28), Typer registration in `engine/src/codestrata/cli/`, Platform entry points.

## Root identity

| Item | Current |
| ---- | ------- |
| Binary | `codestrata` |
| Help positioning | “modernization assessments”; quick start prefers `assess --no-ai` |
| Version line | `CodeStrata 0.1.0` (`package_metadata.PRODUCT_NAME`) |
| Docs pointers | `docs/quick-start.md` · `docs/cli-reference.md` · `docs/troubleshooting.md` (Engine-relative) |

## Command inventory

| Command | Purpose | Audience | AI? | Platform? | Docs | Usability / Phase 9 notes |
| ------- | ------- | -------- | --- | --------- | ---- | ------------------------- |
| `version` | Runtime versions | All | No | No | about/version | Default AI provider printed even for non-AI users |
| `about` | Product blurb + URLs | All | No | No | — | Brand = CodeStrata (good) |
| `init` | Scaffold `codestrata.toml` | Community | No | No | init help | Community Edition wording |
| `doctor` | Env/config checks | Community | No | No | doctor | Good first-run signal |
| `examples` | Sample repos / links | Community | No | No | examples | — |
| `assess` | Primary HTML+JSON assessment | Community | Optional `--with-ai` | No | assess help, report docs | **P0:** empty `ai.bedrock.answer_model` can abort; default title “Modernization Assessment” vs HTML “Engineering Assessment” |
| `scan` | Legacy GitHub clone+analyze | Advanced | No (analysis path) | No | scan help | Marked legacy; still prominent |
| `onboard` | Local knowledge base onboarding | Community | Config-dependent | No* | onboard | *Uses knowledge settings; confusing vs Platform RAG |
| `config` | profile / effective / validate / show | All | No | No | configuration-profiles.md | Solid |
| `mcp` | serve / tools / health | Integrators | No | Extensible | mcp docs | Disabled by default |
| `extensions` | Extension surfaces | Maintainers | No | No | extension docs | Advanced |
| `agent` | Agent Framework workflows | Advanced | Possibly | No | agent-framework.md | Advanced surface in root help |
| `incremental` | Incremental assess opt-in | Advanced | Optional | No | incremental-assessment.md | Explicit opt-in |
| `rules` | Shared Rule Platform inspect | Advanced | No | No | analysis-intelligence | Phase numbering in help |
| `evidence` | Language evidence providers | Advanced | No | No | evidence-providers | Phase numbering |
| `architecture` | Architecture intelligence helpers | Advanced | No | No | architecture docs | Phase numbering |
| `roadmap` | Modernization roadmap helpers | Advanced | No | No | modernization-roadmap.md | Engine roadmap ≠ Platform Strategic Roadmap |
| `report` | Report contract validate | Advanced | No | No | report-contract.md | — |
| `acceptance` | MVP harness | Maintainers | No | No | mvp docs | Not customer-facing |
| `release` | Release readiness helpers | Maintainers | No | No | release-readiness | Not customer-facing |
| `ai` | providers / config / health | Platform/AI | Meta | **Yes** (extension) | Platform RAG CLI | Stub without Platform |
| `enterprise` | Enterprise KG YAML | Advanced/Platform | No | **Yes** | Platform KG docs | Name “Enterprise” vs Platform |
| `repository` | Grounded search/answer | Platform | Yes (answering) | **Yes** | Platform RAG docs | Stub without Platform |

\*Onboard is Engine-local knowledge store (SQLite), not Commercial Platform.

## `assess` options (summary)

| Option | Notes |
| ------ | ----- |
| `--repo` / `-r` | Local path or GitHub URL |
| `--output` / `-o` | Default `reports` |
| `--with-ai` / `--no-ai` | Default **no-ai** |
| `--model-id` | Advisor only; errors if used without `--with-ai` |
| `--report-title` | Default **Modernization Assessment** (inconsistent with HTML brand report name) |
| `--profile` | community\|local\|enterprise\|bedrock\|openai |
| `--quiet` | Suppresses progress |
| Static analysis / PMD flags | Optional |
| Exit codes | Usage ~2; command errors ~1; success 0 (verify AI fallback still 0) |

## Exit-code patterns

Typically `0` success, `1` runtime/config failure, `2` usage (assess). Not fully standardized across all groups → Phase 9 consistency work.

## Proposed Phase 9 CLI actions (no changes now)

1. Fix config validation that aborts assess (P0).
2. Tier help: Primary / Advanced / Maintainer / Platform.
3. Align report title defaults and brand strings.
4. Rename or label `enterprise` CLI as Platform-scoped.
5. Soften phase numbers in customer-facing help.
6. Document exit-code contract.
