# Cloud Assessment Synthesis

Phase 4.7.5 — deterministic synthesis from Cloud assessment inventory.

## Contract

| Item | Value |
| ---- | ----- |
| Assessment schema | `cloud-assessment` **1.2.0** |
| Synthesis version | **1.0.0** |
| Input | Inventories + Findings + rule execution facts |
| Output | Themes, conclusions, recommendations, overall posture summary |
| Gate | `analysis.cloud.include_synthesis` (default `true` when analysis enabled) |

## Themes (emit only when supported)

| Theme | Trigger |
| ----- | ------- |
| Cloud hygiene landscape | Always when synthesis runs |
| Rule execution coverage | Always when synthesis runs |
| Cloud platform adoption | CLOUD-002 findings |
| Multi-cloud presence | CLOUD-001 findings |
| Containerization maturity | CLOUD-010 findings |
| Kubernetes / orchestration adoption | CLOUD-011 findings |
| Infrastructure as Code maturity | CLOUD-020 and/or CLOUD-021 findings |
| Serverless adoption | CLOUD-030 findings |
| Managed cloud service usage | CLOUD-050 findings |
| Cloud deployment automation | CLOUD-040 findings |
| Cloud technology coverage | CLOUD-060 findings **or** ≥3 technology families observed |
| Deployment assets without platform evidence | CLOUD-061 findings |
| No hygiene findings | Zero findings + rules executed |
| Unsupported cloud analysis scope | Documented limitations present |

## Non-claims

Synthesis must not claim the repository is cloud ready, fully portable,
production ready, or free of cloud issues. It must not prescribe migration or
modernization paths.

Severity implications stay informational / low.

Recommendations are observation-oriented and link Finding IDs and Rule IDs.

## Explicit non-scope

- Report integration is Phase **4.7.6** (presentation only; see [report.md](report.md))
- No AI
- No new evidence collectors or rules
- No cloud provider APIs or readiness scoring
