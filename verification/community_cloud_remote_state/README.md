# Slice 17.2 — Bootstrap OpenTofu Remote State

Creates/validates the dedicated S3 OpenTofu remote-state bucket (native S3
lockfile). **No DynamoDB. No production tofu apply. No product infrastructure.**

## Operator bootstrap

```bash
export AWS_PROFILE=codestrata_infra
export AWS_REGION=us-west-2
./infrastructure/scripts/bootstrap-remote-state.sh
```

## Verify

```bash
export AWS_PROFILE=codestrata_infra
export AWS_REGION=us-west-2
PYTHONPATH=. python -m verification.community_cloud_remote_state
```

Report: `.codestrata-artifacts/validation/suites/sv17-2/community-cloud-remote-state-verification.json`

## Non-actions

No Slice 17.3 · no OIDC · no Secrets · no Data Lake · no Lambda/API/ECR · no
ingestion · no production apply · no commit/tag/publish.
