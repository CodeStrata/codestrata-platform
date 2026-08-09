# Slice 17.5 — Community Cloud infrastructure deployment

Verification of production foundation apply (ECR, Data Lake, IAM, logs, image, Lambda, API).

## Verify

```bash
PYTHONPATH=. .venv/bin/python -m verification.community_cloud_infrastructure_deployment
```

Report: `.codestrata-artifacts/validation/suites/sv17-5/community-cloud-infrastructure-deployment-verification.json`

## Evidence

Prefers sanitized files under `infrastructure/production/.local/` when present:

- `apply_evidence.json`
- `image_provenance.json`
- `sv17-5-post.tfplan.json`

Fails closed when infrastructure is not actually deployed (does not invent PASS).

## Non-actions

Slice 17.6 owns runtime secrets · ingestion stays OFF · writer unattached (17.7) · no Insights/Docs deploy ·
no commit/tag/publish by this package.
