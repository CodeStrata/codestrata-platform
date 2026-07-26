# Release Readiness

Phase 5.14 packages CodeStrata so it can be installed and verified on a clean
machine without the development repository environment.

Community Edition packaging (Phase 5.22) builds on this checklist — see
[community-edition.md](community-edition.md) and
[COMMUNITY_EDITION_CHECKLIST.md](COMMUNITY_EDITION_CHECKLIST.md).

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install dist/codestrata-*.whl
# Optional extras:
pip install 'codestrata[mcp]'
pip install 'codestrata[bedrock,openai]'
pip install 'codestrata[development]'
```

Core install supports deterministic `codestrata onboard` / `codestrata assess` with no cloud
credentials. MCP, Bedrock, and OpenAI remain optional extras.

## Packaged resources

Installed under ``codestrata.resources``:

- `config/codestrata.defaults.toml`
- `schemas/assessment/.../AssessmentReport.json`
- `schemas/enterprise/.../Enterprise.json`
- `engineering_knowledge/codestrata-core-v1.yaml`

Also packaged:

- grounded-answer prompts under `codestrata.application.knowledge.answering.prompts`
- HTML branding logo under `codestrata.reporting.assets`

HTML report bodies are generated in code (no separate template files).

## Commands

```bash
codestrata version
codestrata --help
codestrata onboard --help
codestrata report validate --help
codestrata mcp health --config codestrata.toml   # requires [mcp] extra + mcp.enabled
codestrata acceptance run --help
codestrata release check
```

## Clean-install smoke

```bash
python scripts/clean_install_smoke.py
```

Writes `reports/release-readiness/clean-install-smoke.json` and builds wheel/sdist
under `dist/`.

## Release check

```bash
codestrata release check
codestrata release check --skip-smoke   # metadata/resources only
```

Validates package metadata, required resources, CLI registration, schemas,
prompts, default configuration, deterministic provider health, build artifacts,
and clean-install smoke results. Writes `reports/release-readiness/summary.json`.
