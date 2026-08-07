# Slice 12.2 — Cursor Release Surface Removal Verification

Schema: `cursor-release-surface-removal-verification` @ `1.0.0`  
Report: `reports/verification/sv12-2/cursor-release-surface-removal-verification.json`

## Posture

- **VS Code is the only active Community editor extension** in build, package,
  Marketplace, release inventory, version, checksum, license, and publish tooling.
- **No active script enters `cursor-plugin/`** (product already removed in 12.1).
- **No Cursor VSIX / Marketplace packaging** remains in active release docs or
  SV.16 release-artifact checks.
- **Historical Cursor compatibility vocabulary remains** for schema deserialize
  (Slice 12.4 Approach A — retired from active emission/ingestion).
- **Broad documentation/branding cleanup completed in Slice 12.3**.
- **Infrastructure export redesign deferred**.
- **No product schemas changed**.
- **No commit / tag / publish / deploy**.

## Run

```bash
PYTHONPATH=. python -m verification.cursor_release_surface_removal
```

## Tests

```bash
PYTHONPATH=. python -m pytest tests/verification/cursor_release_surface_removal -q
```

## Scope boundary

This package verifies Slice **12.2 only**. Slice 12.3 (documentation/branding)
and Slice 12.4 (client boundary cleanup) are separate packages.
