# Slice 12.1 — Cursor Extension Removal Verification

Schema: `cursor-extension-removal-verification` @ `1.0.0`  
Report: `reports/verification/sv12-1/cursor-extension-removal-verification.json`

## Posture

- **Cursor product source removed** — the `cursor-plugin/` directory is absent (no
  tombstone, no placeholder package).
- **VS Code remains** — `vscode-plugin/` is unchanged and independently testable.
- **Historical Cursor compatibility may remain temporarily** — Engine/Platform
  `cursor_extension` client vocabulary and prior verification reports that mention
  Cursor are intentionally preserved.
- **Active build/release/Marketplace Cursor surfaces were removed in Slice 12.2.**
- **Broad documentation/branding cleanup completed in Slice 12.3**.
- **Telemetry/analytics contract cleanup completed in Slice 12.4** (active vs
  historical client separation; `community-retired-client-policy:1.0`).
- **No product schemas changed** in this slice (Assessment 1.2, telemetry,
  analytics, Community Cloud, Data Lake, provider-platform).
- **No commit / tag / publish / deploy** as part of this verification.

## Run

```bash
PYTHONPATH=. python -m verification.cursor_extension_removal
```

Optional:

```bash
PYTHONPATH=. python -m verification.cursor_extension_removal --skip-vscode-compile --skip-vscode-tests
```

## Tests

```bash
PYTHONPATH=. python -m pytest tests/verification/cursor_extension_removal -q
```

## Scope boundary

This package verifies Slice **12.1** product removal. Slice **12.2** covers
active build/release/Marketplace surface cleanup. Historical verification
reports are not rewritten.

Epic 12 completion: `verification/product_cleanup_repository_split_completion/`
(Slice 12.10). Epic 13 is not started.
