# Architecture — Community Cloud serverless foundation

## Purpose

Slice 7.14 introduces AWS serverless packaging and deployment for the Community
Cloud API as a **production infrastructure foundation**.

The Slice 7.14 deployment proves that the Community Cloud API can be packaged
and served through serverless infrastructure. It does not enable durable
Community event ingestion because production credential verification, shared
event identity, and event sinks are not yet configured.

Slice 8.1 adds `infrastructure/modules/community-data-lake/`: a private S3
foundation with `raw/` and `quarantine/` prefixes. It is composed in production
but remains **unwired** (`enable_ingestion_wire = false`). Ingestion
notifications, Lambda writer attachment, and analytics are deferred.

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
| Community Data Lake bucket / writer IAM doc | `infrastructure/modules/community-data-lake` |
| Data Lake domain contracts | `platform/.../community_cloud_api/data_lake` |

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

## Explicitly out of scope (still deferred)

- Data Lake ingestion wiring / Lambda writer attachment / analytics
- Durable sinks, queues, workers, dashboards
- Cognito / Lambda authorizers / API keys / WAF / custom domains
- Secrets Manager credential lifecycle
- Distributed rate-limit store
- Commercial Platform API deployment

Slice 8.1 **does** provide the unwired Data Lake bucket foundation — see
`docs/community-data-lake.md`.