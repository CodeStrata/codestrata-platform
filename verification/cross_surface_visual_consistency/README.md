# Slice 14.13 — Cross-Surface Visual Consistency

Verification package: `cross-surface-visual-consistency-verification:1.0.0`

Policy: `codestrata-cross-surface-consistency-policy:1.0`  
Contract: `codestrata-cross-surface-consistency-contract:1.0`

## Run

```bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 22
cd /path/to/codestrata-platform
PYTHONPATH=engine/src:platform/src:. .venv/bin/python -m verification.cross_surface_visual_consistency
```

Report: `.codestrata-artifacts/validation/suites/sv14-13/cross-surface-visual-consistency-verification.json`

## Scope

Validates semantic visual consistency across documentation, Assessment HTML,
EIR HTML, VS Code, Marketplace, and API portal surfaces under Design System 1.0.
Does not start Slice 14.14. No commit/tag/publish/deploy.
