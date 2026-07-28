# Contributor Guide

How to develop CodeStrata Engine safely and consistently.

Also see monorepo [CONTRIBUTING.md](../CONTRIBUTING.md),
[coding-standards.md](coding-standards.md), [SECURITY.md](../SECURITY.md),
and the documentation portal [README.md](README.md).

## Development setup

From the **Engine** tree (`engine/` in the monorepo, or `codestrata-engine`):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,bedrock,openai,mcp]'
```

Confirm:

```bash
codestrata version
pytest -q tests/test_cli.py
```

Monorepo maintainers also install Platform per root CONTRIBUTING.md.

## Where docs live

Prefer the journey portal ([README.md](README.md)) over inventing parallel guides.
Reference Governance and Knowledge; do not duplicate them.

## Quality gates (required before PR)

```bash
ruff check .
ruff format --check .
mypy src
pytest
python -m build
```

Documentation changes should also pass:

```bash
pytest tests/docs -q
```

## Guidelines

* Prefer small, focused pull requests.
* Deterministic analysis is the source of truth — AI must not invent findings.
* Match existing package layout (`application` / `domain` / `infrastructure`).
* Do not commit secrets, `.env`, or large `reports/` trees.
* Update docs when CLI, artifacts, or configuration change.
* Never resurrect pre-rename package/CLI/config identifiers in user-facing surfaces.

## Adding a language fixture

1. Create `test-fixtures/sample-<lang>-app/` with a minimal build manifest.
2. Add a short README with `codestrata assess --repo …` instructions.
3. Link it from test-fixtures/README.md.
4. Ensure documentation validation still passes (`tests/docs`).
5. Do **not** add language samples to the public `examples/` (showcase) tree.

## Documentation conventions

* Prefer kebab-case topic files under `docs/`.
* Link related guides instead of duplicating long tables.
* Keep command examples copy-pasteable and validated by `tests/docs`.
* Point troubleshooting at `Fix:` style CLI errors where possible.

## Reporting security issues

See [SECURITY.md](../SECURITY.md). Do not open public issues for vulnerabilities.
