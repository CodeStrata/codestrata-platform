# Contributing to CodeStrata (Community Engine)

Thanks for contributing to the Community Engine.

Full workflow: [docs/contributor-guide.md](docs/contributor-guide.md).
Public docs portal: [https://docs.codestrata.ai](https://docs.codestrata.ai).

## Development setup

Requires Python 3.12+.

From the **codestrata-platform** monorepo:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e "./engine[dev,mcp]"
# Optional Platform surfaces (private):
# python -m pip install -e "./platform[dev,mcp,pgvector]"
```

From a standalone `codestrata-engine` checkout:

```bash
python -m pip install -e ".[dev,mcp]"
```

## Quality gates

```bash
pytest
pytest tests/docs -q
ruff check .
ruff format --check .
mypy src
```

In the monorepo, prefer `mypy engine/src` and root `pytest`.

## Guidelines

* Prefer small, focused pull requests.
* Deterministic analysis remains the source of truth; do not let AI invent
  findings or recommendations.
* Match existing package layout (`src/codestrata/…`, tests under `tests/`).
* Do not commit secrets, `.env` files, or large generated `reports/` trees.
* Update Engine docs under `docs/` when behavior or artifacts change.
* **Documentation visibility:** every new Markdown doc must declare or clearly
  imply whether it is public Community, public contributor, or private
  Platform/internal documentation (prefer
  `<!-- documentation-visibility: public-community|public-contributor|public-contract|private-internal -->`).
  Private classification inventories must not ship in Community exports.
* Platform RAG / Knowledge Graph docs belong under `platform/docs/` in the monorepo.
* Never reintroduce pre-rename package/CLI/config identifiers in user-facing surfaces.
* Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting security issues

See [SECURITY.md](SECURITY.md). Do not open public issues for vulnerabilities.

## License

By contributing, you agree that your contributions are licensed under the MIT
License ([LICENSE](LICENSE)).
