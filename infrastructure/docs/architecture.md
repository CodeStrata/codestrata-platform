# Architecture — Community Cloud serverless foundation

## Purpose

Slice 7.14 introduces AWS serverless packaging and deployment for the Community
Cloud API as a **production infrastructure foundation**.

The Slice 7.14 deployment proves that the Community Cloud API can be packaged
and served through serverless infrastructure. It does not enable durable
Community event ingestion because production credential verification, shared
event identity, and event sinks are not yet configured.

Community Data Lake resources are intentionally deferred. Future S3 buckets,
lifecycle, partitioning, encryption, access, and ingestion notifications will be
added through a separate `infrastructure/modules/data-lake` module.

## Request path

```text
Internet
  → API Gateway HTTP API (HTTPS)
  → AWS_PROXY integration (payload format 2.0)
  → one Lambda function (container image from private ECR)
  → Mangum → FastAPI/ASGI (`create_production_foundation_app`)
  → RouteRegistry (six production routes)
```

Infrastructure does **not** duplicate business routes. A catch-all proxy
forwards to the application. Health is reachable only at `/api/v1/health`
(no root-level health alias).

## Ownership boundary

| Concern | Owner |
| --- | --- |
| Routes, schemas, policies, auth, rate limits, sinks | `platform/.../community_cloud_api` |
| Lambda adapter / production wiring | `platform/.../community_cloud_api/deployment` |
| Dockerfile | `platform/deployment/community-cloud-api/` |
| API Gateway, Lambda, IAM, ECR, logs, throttling | `infrastructure/modules/community-cloud-api` |
| Production composition | `infrastructure/production` |

## Environments

Only `production/` exists. Future `dev/` and `staging/` roots can compose the
same module without moving it. No Terraform workspaces for environment
separation.

## Fail-closed posture

| Capability | Foundation behavior |
| --- | --- |
| Health | Operational |
| Authentication | Enabled; verifier unavailable → protected routes 503 |
| Rate limiting | API Gateway stage throttling + process-local app limiter |
| Event sinks / identity | Unavailable |
| Ingestion durability | Disabled (`CODESTRATA_INGESTION_ENABLED=false`) |

## Explicitly out of scope

- Community Data Lake / S3 ingestion buckets
- Durable sinks, queues, workers, dashboards
- Cognito / Lambda authorizers / API keys / WAF / custom domains
- Secrets Manager credential lifecycle
- Distributed rate-limit store
- Commercial Platform API deployment
