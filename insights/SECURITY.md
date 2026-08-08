# Security Policy — codestrata-insights

This private repository contains the CodeStrata Community Insights frontend
application. It is an internal analytics surface, not a public Community
product package.

## Reporting

Report security issues through the CodeStrata private security channel used for
Community Cloud and Insights hosting controls. Do not file public issues that
include credentials, session cookies, or account identifiers.

## Boundaries

- No production secrets are stored in this repository
- `.env` files are local-only and must not be committed
- Authentication cookies and CSRF tokens are runtime-only
- Backend APIs remain on the private Platform Community Cloud surface

## Validation posture

Local validation uses `npm ci`, `npm run typecheck`, `npm test`, and
`npm run build` without production deployment.
