# CodeStrata public reports delivery (Slice 17.16)

Thin Cloudflare Worker + branded landing for `https://reports.codestrata.ai`.

Flow:

```text
Browser → reports.codestrata.ai/          → static landing (public/)
       → reports.codestrata.ai/r/<opaque-id>
       → api.codestrata.ai/api/v1/reports/<opaque-id>
       → Lambda → private report-artifact S3
```

`/` is a minimal branded page (no report directory or discoverable IDs).
Browser branding (`favicon.ico` / `favicon.png` / `apple-touch-icon.png`) matches
docs + Insights (same bytes as `docs/public/`).
`/r/*` is handled by the Worker (`run_worker_first`) and proxied to the API.

Deploy (operator, with Cloudflare token out of band):

```bash
cd reports
npm install
npx wrangler deploy
```

Does not host report HTML statically. Does not expose S3.
Cache on `/r/*` is bounded (`max-age=60`) so revoke can take effect.
