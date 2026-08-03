# Security boundary

## Private ownership

The entire `infrastructure/` tree is private and excluded from Community/public
repository exports. Future extraction target: `codestrata-infrastructure`.

## Secrets

Never commit:

- AWS access keys / secret keys
- Community client tokens (`cscc_v1_…`)
- Bearer tokens
- Private keys
- Provider API keys
- Passwords
- Live account secrets

`terraform.tfvars.example` uses unmistakable placeholders only
(e.g. `REPLACE_ME`, documentation account `123456789012`).

No Secrets Manager resources in Slice 7.14 — credential lifecycle is not
designed yet.

## Authentication

Production wiring keeps authentication **enabled** with an **unavailable**
verifier. Protected ingestion returns fail-closed 503. Health stays public.

Future requirements (not implemented):

- Secure credential issuance
- Secure verifier storage
- Rotation and revocation
- Deployment adapter for production verification

Do not weaken authentication by disabling it.

## Rate limiting

- API Gateway stage throttling: deployment-level outer protection
- Application limiter: process-local defense-in-depth
- Authenticated distributed client quotas: **not** implemented
- No DynamoDB/Redis rate-limit store in this slice

## Logging

CloudWatch log group with explicit retention (default 30 days). Application
structured logs only — no request bodies, Authorization headers, raw IPs,
event IDs, source paths, prompts, or repository metadata.

## IAM

Lambda execution role is least privilege (CloudWatch logs to the function log
group). No S3/DB/queue/Secrets Manager grants. See `policies/`.

## Network

- HTTPS via API Gateway
- No custom domain, CORS changes, WAF, API keys, or authorizers in this slice
- No VPC attachment for the Lambda
