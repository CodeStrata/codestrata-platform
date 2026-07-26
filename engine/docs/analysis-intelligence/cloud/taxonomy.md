# Cloud Taxonomy

Phase 4.7.1 introduces `CloudCategory` as a repository-observable capability
taxonomy for future Cloud Intelligence rules and assessment metadata.

| Category | Serialized value |
| -------- | ---------------- |
| Externalized configuration | `cloud.externalized_configuration` |
| Statelessness | `cloud.statelessness` |
| Portability | `cloud.portability` |
| Container readiness | `cloud.container_readiness` |
| Managed service compatibility | `cloud.managed_service_compatibility` |
| Deployment automation | `cloud.deployment_automation` |
| Configuration | `cloud.configuration` |
| Runtime | `cloud.runtime` |
| Miscellaneous | `cloud.miscellaneous` |
| Unknown | `cloud.unknown` |

Methodology taxonomy rows that use kebab-case (for example
`cloud.externalized-configuration`) coerce to the snake_case enum values above.

## Non-goals (this phase)

- No cloud provider detection
- No rule implementations for these categories
- No readiness / compliance scoring

Unknown or unmapped inputs coerce to `cloud.unknown`.
