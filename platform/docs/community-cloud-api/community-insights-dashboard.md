# Community Insights Dashboard (Slice 15.10)

Presentation-only dashboard for authenticated aggregate `MetricResult` values.

## Design authority

CodeStrata Design System 1.0 (`design-system/`). Insights consumes the exported
token copy at `insights/public/design-tokens/tokens.css`. No dashboard-specific
palette or Chart.js/CDN charts.

## Visualization

Local CSS/SVG horizontal bar charts plus accessible data tables. No fabricated
time series. Validation dataset shows **size**, not growth history.

## API

One authenticated `GET /api/v1/insights/api/overview` per load/refresh.

## Boundaries

Auth does not relax privacy. Production ingestion remains disabled. Slice 15.11
(validation/hardening epic closure) has not started.
