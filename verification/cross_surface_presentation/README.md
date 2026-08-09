# Cross-surface presentation verification (Slice 14.7)

Schema: `cross-surface-presentation-verification:1.0.0`  
Policy: `codestrata-cross-surface-presentation-policy:1.0`

## Purpose

Verify one authoritative Design System presentation contract across Docs,
Assessment HTML, EIR HTML, VS Code (native exceptions), and Marketplace (raster
exceptions). This is **not** a visual redesign.

## Run

```bash
.venv/bin/python -m verification.cross_surface_presentation
pytest tests/verification/cross_surface_presentation -q
```

Report: `.codestrata-artifacts/validation/suites/sv14-7/cross-surface-presentation-verification.json`

## Boundaries

- Design System remains **1.0** (additive contracts; no version bump)
- Charts / score-risk visualization → Slice **14.8**
- Navigation IA → **14.9**
- Universal assets → **14.10**
- Accessibility acceptance → **14.11** (complete)
- Documentation deployment → **14.12** (not started)
- No runtime/domain behavior change
- No commit / tag / publish / deploy
