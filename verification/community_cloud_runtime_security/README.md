# Slice 17.6 — Community Cloud runtime security

Verification of production runtime security: Insights auth secrets (identifiers +
operational values in Secrets Manager only), Lambda IAM posture, ingestion OFF,
Data Lake writer unattached (deferred to 17.7).

## Verify

```bash
PYTHONPATH=. .venv/bin/python -m verification.community_cloud_runtime_security
```

Report: `.codestrata-artifacts/validation/suites/sv17-6/community-cloud-runtime-security-verification.json`

## Evidence

Prefers sanitized files under `infrastructure/production/.local/` when present:

- `secrets_evidence.json`
- `runtime_security_evidence.json`

Fails closed on critical gates when secrets/IAM operational evidence is absent
(does not invent PASS).

## Non-actions

Writer attachment and ingestion enablement are owned by Slice 17.7
(`verification/community_cloud_production_ingestion`).
