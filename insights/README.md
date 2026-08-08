# CodeStrata Community Insights

Internal Community Insights dashboard for CodeStrata Community Edition adoption analytics.

| Field | Value |
| --- | --- |
| Package | `codestrata-insights` |
| Future repository | `codestrata-insights` (private) |
| Future host | `insights.codestrata.ai` |
| Stack | React + Vite + TypeScript (SPA, no SSR) |

## Commands

```bash
npm ci
npm test
npm run build
```

## Boundaries

- Platform owns aggregation / MetricResult / privacy / future API + auth validation
- This app owns presentation only — **does not compute metric semantics**
- No S3, AWS SDK, Secrets Manager, or credentials in the browser
- Authentication is deferred to Slice 15.9
- Charts/visualizations deferred to Slice 15.10
- Production default API client is **unavailable / not connected** (synthetic mocks are tests/dev only)

## Design System

Consumes CodeStrata Design System 1.0 tokens via `public/design-tokens/tokens.css` (exportable copy of authoritative tokens).
