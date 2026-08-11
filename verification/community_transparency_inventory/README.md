# Community Transparency Inventory (Slice 18.1)

Inventory + source-of-truth mapping only. Runtime/contracts/infrastructure are
authoritative over docs. Slice 18.2 is not started.

## Run

```bash
export PYTHONPATH=platform/src:engine/src
.venv/bin/python -m verification.community_transparency_inventory
.venv/bin/python -m pytest tests/verification/community_transparency_inventory -q
```

## Outputs

`.codestrata-artifacts/validation/suites/sv18-1/community-transparency-inventory-verification.json`
