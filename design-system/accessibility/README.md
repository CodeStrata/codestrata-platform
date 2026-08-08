# Accessibility

Policy: `codestrata-accessibility-responsive-policy:1.0` (Slice 14.11)  
Contract: `design-system/contracts/accessibility.json`  
Rules: `design-system/accessibility/rules.json`

| Concern | Rule |
| ------- | ---- |
| Contrast | Ink on canvas and teal-dark on white must meet WCAG AA for text/UI |
| Focus | Theme-aware `:focus-visible` via `--cs-focus` (docs 3px/3px; reports 2px/2px) |
| Skip link | Required on marketing/docs shells |
| Keyboard | All interactive controls reachable; no mouse-only workflows |
| Motion | Honor `prefers-reduced-motion`; disable nonessential transitions |
| Touch | Interactive targets ≥ ~34–44px where practical |
| Color alone | Status never communicated by color only — pair with label/icon |
| Typography | Do not shrink body below 14px on primary reading surfaces without cause |

Light and dark themes both required for accessibility planning.
