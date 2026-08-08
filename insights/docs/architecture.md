# Community Insights Application Architecture

## Stack decision

**React + Vite + TypeScript static SPA.**

Rationale: internal analytics dashboard will call authenticated Platform APIs later; no SSR/Next.js requirement; minimal dependencies; Cloudflare-static hosting ready; independently exportable to `codestrata-insights`.

## Authority

- Pre-cutover source: monorepo `insights/`
- Post-cutover: private `codestrata-insights` repository
- Host: `insights.codestrata.ai` (not deployed in Slice 15.8)
