# Slice 16.1 — Repository Inventory & Classification

Audit-only inventory of the monorepo for Epic 16 cleanup planning.

## Authority

- Policy: `repository-cleanup-policy:1.0` (`platform/policies/repository_cleanup_policy.json`)
- Schema: `repository-inventory-verification:1.0.0`
- Report: `reports/verification/sv16-1/repository-inventory-verification.json`

## Boundaries

- No deletions, renames, moves, or runtime behavior changes in this slice
- Cleanup actions deferred to Slice 16.2 (`Slice 16.2 documentation cleanup may proceed; Slice 16.3 forbidden`)
- No commit / tag / publish / deploy

## Run

```bash
python -m verification.repository_inventory
```
