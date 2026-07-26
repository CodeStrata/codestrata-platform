# Phase 4.7.3 — Cloud Hygiene Rules Review

**Date:** 2026-07-25  
**Artifacts:** `reports/dogfood-phase-4-7-3/` (gitignored)  
**Pack:** `cloud.core` **1.0.0** (11 hygiene rules)

## Recommendation

**Accept Phase 4.7.3.** Rules consume only
`AggregatedRepositoryCloudEvidence`, emit shared Findings with stable IDs,
Informational/Low severity, and observation-only remediation notes.
No assessment inventory, synthesis, scoring, reporting, AI, new collectors,
or git commit.

## Pipeline

```text
Repository Cloud Evidence
        ↓
cloud.core SharedRules
        ↓
Shared Findings
        ↓
(Phase 4.7.4 Assessment)
```

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Evidence | 0 candidates |
| Findings | **0** |
| Repeat-run bytes | **byte-identical** |

Empty evidence correctly yields no Cloud Findings.

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Technologies | `devcontainer`, `docker`, `docker_compose`, `github_actions`, `kubernetes` |
| Findings | **5** |
| Rules | CLOUD-010, CLOUD-011, CLOUD-040, CLOUD-060, CLOUD-061 |
| Repeat-run bytes | **byte-identical** |

CLOUD-061 fires (deployment assets, no AWS/Azure/GCP platform markers).

## Cloud-native fixture dogfood

| Field | Value |
| ----- | ----- |
| Technologies | `aws`, `docker`, `docker_compose`, `github_actions`, `kubernetes`, `s3`, `serverless_framework`, `terraform` |
| Findings | **8** |
| Rules | CLOUD-002, CLOUD-010, CLOUD-011, CLOUD-020, CLOUD-030, CLOUD-040, CLOUD-050, CLOUD-060 |
| Repeat-run bytes | **byte-identical** |

CLOUD-061 correctly suppressed (AWS platform present). CLOUD-001/021 not
triggered (single platform; single IaC kind in this fixture).

## Validation

- Unit tests: every rule + pack registration + determinism + gate defaults
- Ruff + mypy on changed packages: pass
- Assessment inventory / synthesis / reporting / AI / git commit: **not added**
