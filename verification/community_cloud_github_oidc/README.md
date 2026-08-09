# Slice 17.3 — GitHub → AWS OIDC identity

Creates/validates the GitHub Actions OIDC provider + production deployment role
with **minimal dedicated remote-state S3 access**.

## Bootstrap

```bash
export AWS_PROFILE=codestrata_infra
export AWS_REGION=us-west-2
# First: attach infrastructure/bootstrap/github-oidc/operator-iam-bootstrap-policy.json
./infrastructure/scripts/bootstrap-github-oidc.sh
```

## Verify

```bash
export AWS_PROFILE=codestrata_infra
export AWS_REGION=us-west-2
PYTHONPATH=. .venv/bin/python -m verification.community_cloud_github_oidc
```

Report: `.codestrata-artifacts/validation/suites/sv17-3/community-cloud-github-oidc-verification.json`

## Non-actions

No Slice 17.4 · no production apply · no product infra · no application Secrets ·
no ingestion · no Insights/Docs deploy · no commit/tag/publish.
