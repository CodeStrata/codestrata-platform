# Deployment IAM policy guidance (Slice 7.14)

This document describes the **human/CI deployer** permission boundary for the
Community Cloud API production foundation. It is guidance, not a live IAM
policy attached to an AWS account.

## Lambda execution role (runtime)

The OpenTofu module grants the Lambda execution role:

- `logs:CreateLogStream` / `logs:PutLogEvents` on the function log group
- `ecr:GetDownloadUrlForLayer` / `ecr:BatchGetImage` /
  `ecr:BatchCheckLayerAvailability` on the private repository
- `ecr:GetAuthorizationToken` with `Resource = "*"` — **AWS-documented
  exception** (authorization tokens cannot be scoped to a repository ARN)

No grants for:

- S3 (including future data lake)
- DynamoDB
- SQS / SNS / Kinesis
- Secrets Manager / SSM Parameter Store
- IAM administration
- Broad `Action = "*"`

Reference JSON shape: `lambda-execution-policy.json` (illustrative ARN pattern).

## Deployer identity (plan/apply/push)

Operators who plan/apply infrastructure or push images should use a dedicated
role with least privilege, typically limited to:

- Creating/updating the module resources in this slice
- Pushing images to the private ECR repository
- Reading CloudWatch logs for the function

They must **not** receive:

- Organization-wide admin
- Cross-account customer cloud access
- Secrets for Community client tokens
- Unrelated production data stores

## Wildcards

Any future wildcard must be reviewed and documented with:

1. Why AWS requires it
2. The narrowest workable alternative considered
3. Residual risk

Slice 7.14 avoids wildcards in the Lambda execution policy.

## Secrets

Deployers must not commit credentials. Use the AWS credential chain /
temporary credentials. Community client tokens are out of scope until a
credential lifecycle design exists.
