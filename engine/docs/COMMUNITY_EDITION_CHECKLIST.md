# Community Edition release checklist

Use this checklist before tagging a public GitHub Community Edition release.

## Scope and messaging

- [ ] [docs/community-edition.md](community-edition.md) matches shipped defaults
- [ ] README feature matrix distinguishes Community vs future Enterprise/Platform
- [ ] Enterprise KG documented as optional / disabled by default
- [ ] No claims of hosted multi-tenancy, billing, or SSO

## Governance files

- [ ] [LICENSE](../LICENSE) (MIT)
- [ ] [NOTICE](../NOTICE)
- [ ] [SECURITY.md](../SECURITY.md)
- [ ] [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
- [ ] [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] [SUPPORT.md](../SUPPORT.md)
- [ ] [CHANGELOG.md](../../CHANGELOG.md) updated for the release
- [ ] [docs/RELEASE_NOTES-0.1.0.md](RELEASE_NOTES-0.1.0.md) (or versioned notes) reviewed

## Metadata

- [ ] `pyproject.toml` version matches `codestrata.__version__` / branding
- [ ] Project URLs point at the public GitHub repository
- [ ] Classifiers and license metadata correct
- [ ] `codestrata release check` passes

## Examples and docs

- [ ] All five language samples assess cleanly
- [ ] Sample reports present under `test-fixtures/sample-reports/`
- [ ] Quick start / tutorial / CLI reference links resolve (`pytest tests/docs`)
- [ ] No stale pre-rename wheel / package names in docs

## Packaging validation

- [ ] `python -m build` produces `codestrata-*.whl` and sdist
- [ ] Fresh venv: `pip install dist/codestrata-*.whl`
- [ ] `codestrata version` / `codestrata assess --repo test-fixtures/sample-js-app …`
- [ ] HTML `report.html` generated
- [ ] Optional: `pip install 'codestrata[mcp]'` and `codestrata mcp --help`
- [ ] Optional: `python scripts/clean_install_smoke.py`

## Quality gates

- [ ] `ruff check .`
- [ ] `mypy src`
- [ ] `pytest` (full suite)
- [ ] `pytest tests/docs`

## GitHub presentation

- [ ] README badges render
- [ ] Topics / description set on the GitHub repo
- [ ] Default branch protected as desired
- [ ] Security advisories path verified

## Release

- [ ] Tag `v0.1.0` (or target version)
- [ ] GitHub Release attaches wheel/sdist + release notes
- [ ] Announce install: `pip install codestrata` (when published to PyPI) or
      `pip install dist/codestrata-*.whl`
