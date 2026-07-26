# CodeStrata 0.1.0 — Release Notes (draft)

**Edition:** Community Edition (open source, MIT)  
**Status:** Draft for public GitHub release  
**Date:** 2026-07-26

## Highlights

CodeStrata 0.1.0 is the first Community Edition packaging of the deterministic
modernization assessment engine:

* Assess local or GitHub repositories without cloud credentials (deterministic mode)
* Multi-language detection and evidence: Java, JavaScript/TypeScript, Python, PHP, C#/.NET
* Deterministic findings and recommendations with HTML Report v2 + JSON artifacts
* Optional one-call Amazon Bedrock enrichment
* Local knowledge store, MCP server (optional extra), and Agent Framework
* Execution profiles (`community`, `local`, `enterprise`, `bedrock`, `openai`)
* Developer docs: quick start, tutorial, CLI reference, troubleshooting

## Install

From a built distribution:

```bash
python -m venv .venv
source .venv/bin/activate
pip install dist/codestrata-0.1.0-py3-none-any.whl
codestrata version
codestrata assess --repo test-fixtures/sample-js-app --output reports --no-ai
```

From a clone (development):

```bash
pip install -e ".[dev,mcp]"
```

Optional extras: `bedrock`, `openai`, `mcp`, `pgvector`, `dev`.

## Community Edition scope

Included by default: repository assessment, local graphs, deterministic rules,
HTML/JSON reports, local MCP/agents when enabled.

Enterprise Knowledge Graph and future Platform services (SSO, billing,
multi-tenancy) are **not** Community defaults. See
[community-edition.md](community-edition.md).

## Sample reports

Golden HTML/JSON samples for each language live under
[test-fixtures/sample-reports/](../../test-fixtures/sample-reports/README.md).

## Breaking / rename notes

This release uses the **CodeStrata** package and CLI exclusively. Pre-rename
package and CLI names are not shipped. The product rename was completed in
Phase 5.16 (see [ROADMAP.md](../../ROADMAP.md)).

## Known limitations

* Alpha software (`Development Status :: 3 - Alpha`)
* Many analysis packs are feature-gated and off by default
* Assessment Framework scoring / CTO report methodology is partially ahead of runtime
* PyPI publication may follow the initial GitHub release

## Verification

```bash
codestrata release check
pytest
ruff check .
mypy src
```

Full history: [CHANGELOG.md](../../CHANGELOG.md).  
Checklist: [COMMUNITY_EDITION_CHECKLIST.md](COMMUNITY_EDITION_CHECKLIST.md).
