# Slice 12.3 — Cursor Documentation and Branding Removal

Schema: `cursor-documentation-removal-verification` @ `1.0.0`  
Report: `.codestrata-artifacts/validation/suites/sv12-3/cursor-documentation-removal-verification.json`

## Posture

- **VS Code** is the only supported Community editor extension in current docs.
- No active Cursor installation, usage, Marketplace, or publish instructions.
- No active Cursor screenshots / exclusive branding assets.
- Historical `cursor_extension` vocabulary retained for Slice **12.4**.
- Runtime code and product schemas unchanged.
- No commit / tag / publish / deploy.

## Run

```bash
PYTHONPATH=. python -m verification.cursor_documentation_removal
```

## Tests

```bash
PYTHONPATH=. python -m pytest tests/verification/cursor_documentation_removal -q
```
