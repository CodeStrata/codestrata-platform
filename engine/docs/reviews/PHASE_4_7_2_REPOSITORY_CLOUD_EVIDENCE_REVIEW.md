# Phase 4.7.2 — Repository Cloud Evidence Review

**Date:** 2026-07-25  
**Artifacts:** `reports/dogfood-phase-4-7-2/` (gitignored)  
**Schema:** `repository-cloud-evidence` **1.0.0**  
**Artifact:** `repository-cloud-evidence.json`  
(`codestrata.repository_cloud_evidence`)

## Recommendation

**Accept Phase 4.7.2.** Platform evidence collects deterministic
repository-observable cloud technology and deployment signals only.
No Cloud rules, Findings, assessment inventory, synthesis, report integration,
provider API calls, or readiness scores were added.

## Evidence ownership

| Concern | Owner |
| ------- | ----- |
| Path discovery + content confirmation | Platform `repository_cloud` evidence |
| Cloud Intelligence interpretation | Deferred (future Cloud rules) |
| Findings / severity / remediation | Not in this phase |

Collectors do not import `codestrata.domain.cloud` / `codestrata.application.cloud` and do
not emit Findings.

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Schema / version | `repository-cloud-evidence` / `1.0.0` |
| Bundle ID | `cloud-evidence:8eb31150bec10500` |
| Candidates | 0 |
| Technologies | none |
| Repeat-run bytes | **byte-identical** (fixed inventory) |

Manual notes:

- Enterprise `*-service.yaml` examples are **not** misclassified as Kubernetes.
- No absolute paths, Findings, or readiness scores in the artifact.
- Empty result is valid: CodeStrata is not a cloud-native application repo.

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Schema / version | `repository-cloud-evidence` / `1.0.0` |
| Bundle ID | `cloud-evidence:21f39c3b711ba0ca` |
| Candidates | 8 |
| Technologies | `devcontainer`, `docker`, `docker_compose`, `github_actions`, `kubernetes` |
| Containers | Dockerfile, docker-compose, devcontainer |
| Orchestration | `k8s/db.yml`, `k8s/petclinic.yml` |
| Deployment | GitHub Actions workflows (including cluster deploy) |
| Repeat-run bytes | **byte-identical** |

## Cloud-native fixture dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Candidates | 5 |
| Technologies | `aws`, `docker`, `github_actions`, `kubernetes`, `s3`, `serverless_framework`, `terraform` |
| Managed services | S3 (Terraform `aws_s3_bucket`) |
| Platforms | AWS (provider + serverless) |
| Repeat-run bytes | **byte-identical** |

## Validation

- Focused unit tests: package boundary, defaults, discovery false positives,
  confirmation levels, dedupe, deterministic serialization
- Ruff + mypy on changed packages: pass
- Rules / assessment / inventory / synthesis / reporting / AI / git commit:
  **not added**
