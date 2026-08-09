# Contributing to CodeStrata

This monorepo (`codestrata-platform`) is the private source of truth.

## Where to start

| Audience | Guide |
| -------- | ----- |
| New developers (Engine) | [engine/docs/README.md](engine/docs/README.md) portal · [quick-start.md](engine/docs/quick-start.md) |
| New maintainers | [README.md](README.md) then [platform/README.md](platform/README.md) |
| Community Engine contributors | [engine/CONTRIBUTING.md](engine/CONTRIBUTING.md) · [engine/docs/contributor-guide.md](engine/docs/contributor-guide.md) |
| Platform package developers | [platform/docs/getting-started.md](platform/docs/getting-started.md) |
| Governance (how we build) | [governance/README.md](governance/README.md) |
| Engineering Knowledge (what we know) | [knowledge/README.md](knowledge/README.md) |
| Coding standards | [governance/standards/CODING_STANDARDS.md](governance/standards/CODING_STANDARDS.md) |
| Design System | [design-system/README.md](design-system/README.md) (authoritative) |
| Historical design notes | [governance/assets/DESIGN-SYSTEM.md](governance/assets/DESIGN-SYSTEM.md) |
| Release history | [CHANGELOG.md](CHANGELOG.md) · [ROADMAP.md](ROADMAP.md) (archive candidate) |
| Ecosystem architecture | [ARCHITECTURE.md](ARCHITECTURE.md) · [engine/docs/architecture-guide.md](engine/docs/architecture-guide.md) |
| Documentation cleanup | [platform/docs/repository-cleanup/community-documentation-cleanup.md](platform/docs/repository-cleanup/community-documentation-cleanup.md) |
| Documentation registry (authoritative) | [governance/DOCUMENTATION_REGISTRY.md](governance/DOCUMENTATION_REGISTRY.md) |
| Documentation inventory (historical) | [governance/DOCUMENTATION_INVENTORY.md](governance/DOCUMENTATION_INVENTORY.md) |
| Public API / SDK contracts | [governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md](governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md) |

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
* Every new document must declare or clearly imply visibility: public Community,
  public contributor, or private Platform/internal (see `docs/CONTRIBUTING.md`
  and `engine/CONTRIBUTING.md`). Do not publish private classification inventories.
