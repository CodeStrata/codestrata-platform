# Visualization (Slice 14.8)

Policy: `codestrata-visualization-policy:1.0`  
Contract: `design-system/contracts/visualization.json`

## Purpose

Standardize how engineering **scores, risk, severity, status, confidence, and
charts** are visualized across Assessment HTML and commercial EIR HTML.

Domain truth remains authoritative. This slice does **not** change scoring,
thresholds, or assessment findings.

## Grammar

```
domain state → semantic visualization role → Design System token → surface CSS
```

### Risk / severity

Uses `risk_colors`. Markers + labels required (not color-only).

### Status

Uses `status_colors`. Distinct roles for success, partial, failure, unavailable,
and **not_assessed** (must not look like success).

### Confidence

Uses informational/neutral styling. Confidence is **evidence strength**, not
repository health. Must not map low confidence to critical/red.

### Scores

Catalogued per domain metric. **No** invented universal CodeStrata score.
Zero findings does **not** imply Healthy/Passed/Safe/Secure.

### Charts

Foundation contract only. Current Assessment/EIR surfaces use count cards/KPIs —
no SVG chart library introduced. Prefer CSS or deterministic server SVG later;
never CDN/JS.

## Consumers

| Consumer | Scope |
| --- | --- |
| Assessment HTML | severity badges, status badges, empty/not-assessed |
| EIR HTML | severity badges, confidence indicator |
| Docs | Assessment interpretation only |
| Marketplace | Assessment screenshot truthfulness |
| VS Code | wording only — no health dashboard |

## Deferred

- Report navigation / IA → **14.9**
- Universal assets → **14.10**
- Accessibility acceptance → **14.11** (complete)
- Documentation deployment → **14.12** (not started)
