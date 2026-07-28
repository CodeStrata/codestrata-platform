# CI Readiness — codestrata-docs

Assumptions for a future standalone GitHub Actions (or equivalent) workflow.
**This phase does not deploy.**

## Suggested jobs

1. **Setup** — Node.js 20 LTS
2. **Install** — `npm ci`
3. **Format** (optional) — Prettier on Markdown when introduced
4. **Build** — `npm run build`
5. **Validate** — `npm test` (build + `scripts/validate.mjs`)
6. **Artifact** — upload `.vitepress/dist`
7. **Accessibility** (optional follow-up) — axe/pa11y against preview; not required to PASS this foundation

## Runtime

- Validated locally on the contributor machine OS used for this phase
- Do not claim multi-OS matrix until executed in CI

## Deployment boundary

CI may build and validate. Production publish to `docs.codestrata.ai` is a
separate, explicit workflow (see [DEPLOYMENT.md](./DEPLOYMENT.md)).
