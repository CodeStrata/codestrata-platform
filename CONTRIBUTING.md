# Contributing to CodeStrata

This monorepo (`codestrata-platform`) is the private source of truth.

## Where to start

| Audience | Guide |
| -------- | ----- |
| New maintainers | [README.md](README.md) then [platform/README.md](platform/README.md) |
| Community Engine contributors | [engine/CONTRIBUTING.md](engine/CONTRIBUTING.md) · [engine/docs/contributor-guide.md](engine/docs/contributor-guide.md) |
| Platform package developers | [platform/docs/getting-started.md](platform/docs/getting-started.md) |
| Current direction | [ROADMAP.md](ROADMAP.md) |
| Ecosystem architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "./engine[dev,mcp]"
pip install -e "./platform[dev,mcp,pgvector]"
```

## Quality gates

Prefer the canonical verifier:

```bash
python scripts/verify_release.py
# Faster structural export check (default):
python scripts/verify_release.py
# Full Engine fresh-venv export smoke:
python scripts/verify_release.py --full-export-install
```

Or run steps individually:

```bash
ruff check .
mypy engine/src
pytest
python scripts/security_check.py
python scripts/validate-public-exports.py --skip-install
```

Live product acceptance (heavy): `codestrata acceptance run`.  
Packaging smoke: `python scripts/clean_install_smoke.py`.  
Showcases (network): `python scripts/fetch_example.py` / `python scripts/run_showcase.py`.

## Rules

* Land changes here first; never develop in generated public mirrors.
* Do not commit secrets or large `reports/` trees.
* Preserve Platform → Engine dependency direction.
* Prefer linking to canonical docs over copying content.
