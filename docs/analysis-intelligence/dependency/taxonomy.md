# Dependency Role Taxonomy

Technology-neutral engineering roles for Dependency Intelligence
(`DependencyRole`).

Serialized values use the `dependency.<role>` namespace. Unknown inputs coerce
safely to `dependency.unknown`.

| Role | Serialized value |
| ---- | ---------------- |
| Runtime framework | `dependency.runtime_framework` |
| Runtime library | `dependency.runtime_library` |
| Build tool | `dependency.build_tool` |
| Build plugin | `dependency.build_plugin` |
| Test framework | `dependency.test_framework` |
| Test library | `dependency.test_library` |
| Persistence | `dependency.persistence` |
| Database driver | `dependency.database_driver` |
| Messaging | `dependency.messaging` |
| Serialization | `dependency.serialization` |
| Logging | `dependency.logging` |
| Observability | `dependency.observability` |
| Networking | `dependency.networking` |
| Cloud SDK | `dependency.cloud_sdk` |
| Security library | `dependency.security_library` |
| Internal library | `dependency.internal_library` |
| Development tool | `dependency.development_tool` |
| Third-party library | `dependency.third_party_library` |
| Unknown | `dependency.unknown` |

## Explicit non-goals

- Package-manager scopes (Maven `compile`/`test`, npm `devDependencies`, …)
- Ecosystem package classification in Phase 4.4.1
- Equating these roles with CVE severity or license risk

Package-manager concepts belong to Dependency Evidence normalization.
