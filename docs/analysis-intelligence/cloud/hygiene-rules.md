# Cloud Hygiene Rules

Phase **4.7.3** — `cloud.core` @ **1.0.0**

Rules consume **only** in-memory `AggregatedRepositoryCloudEvidence`.
They do not re-read repository files, call cloud provider APIs, invent
readiness scores, or emit modernization recommendations.

Human aliases **CLOUD-001** … **CLOUD-061** map to machine IDs
`cloud.cloud-00N`.

## Configuration

```toml
[evidence.repository_cloud]
enabled = true

[rules]
enabled = true

[rules.cloud]
enabled = true
```

All gates default to **disabled**. Rules never trigger evidence collection.
Evidence may run without rules. Enabling `[rules.cloud]` does **not** enable
`[analysis.cloud]` assessment inventory/synthesis (still empty / deferred).

Per-rule toggles (default enabled when the pack is on):

```toml
[rules.cloud.cloud_001]
enabled = true
# … cloud_002, cloud_010, cloud_011, cloud_020, cloud_021,
#   cloud_030, cloud_040, cloud_050, cloud_060, cloud_061
```

## Rule catalog

| Alias | Rule ID | Trigger | Severity | Category |
| ----- | ------- | ------- | -------- | -------- |
| CLOUD-001 | `cloud.cloud-001` | ≥2 known cloud platforms | LOW | `cloud.portability` |
| CLOUD-002 | `cloud.cloud-002` | Exactly 1 known platform (suppressed when CLOUD-001 matches) | INFORMATIONAL | `cloud.runtime` |
| CLOUD-010 | `cloud.cloud-010` | Containerization artifacts | INFORMATIONAL | `cloud.container_readiness` |
| CLOUD-011 | `cloud.cloud-011` | Kubernetes / Helm / OpenShift | INFORMATIONAL; LOW if ≥2 kinds | `cloud.container_readiness` |
| CLOUD-020 | `cloud.cloud-020` | Any known IaC technology | INFORMATIONAL | `cloud.configuration` |
| CLOUD-021 | `cloud.cloud-021` | ≥2 distinct IaC technologies | LOW | `cloud.portability` |
| CLOUD-030 | `cloud.cloud-030` | Serverless artifacts | INFORMATIONAL | `cloud.runtime` |
| CLOUD-040 | `cloud.cloud-040` | Cloud-related deployment pipeline systems | INFORMATIONAL | `cloud.deployment_automation` |
| CLOUD-050 | `cloud.cloud-050` | Managed service markers | INFORMATIONAL; LOW if ≥3 services | `cloud.managed_service_compatibility` |
| CLOUD-060 | `cloud.cloud-060` | ≥3 distinct evidence families | INFORMATIONAL | `cloud.miscellaneous` |
| CLOUD-061 | `cloud.cloud-061` | Deployment assets present, zero known platforms | LOW | `cloud.configuration` |

Severity is limited to **Informational** and **Low**. No Medium/High/Critical.

## Precision notes

- Confidence is derived only from observed confirmation levels
  (structurally confirmed → HIGH; inspected/declared/configured → MEDIUM;
  otherwise LOW).
- CLOUD-060 does **not** claim the repository is cloud-native or ready.
- CLOUD-061 does **not** claim cloud usage is absent — only that no AWS/Azure/GCP
  platform markers were observed alongside deployment assets.
- Empty / unusable evidence → rules are not applicable (no Findings).

## Finding identity

Finding IDs use `finding:{rule_id}:{digest}` from stable subject keys.
Shuffle of input fact order must not change Finding IDs or serialized bytes.

## Privacy

Findings may include relative paths and technology identifiers. Absolute
filesystem paths and source bodies are never serialized. Remediation text is
an observation-only note (no modernization advice).

## Explicit exclusions (this phase)

- No Cloud assessment inventory / themes / conclusions
- No synthesis or scoring
- No report adapter / CTO narrative
- No AI
- No new evidence collectors

Zero findings does **not** mean the repository is cloud ready or free of
cloud debt.

## Related

- Evidence: [../repository-cloud-evidence.md](../repository-cloud-evidence.md)
- Configuration: [configuration.md](configuration.md)
- Pack package: `aimf.application.rules.cloud`
