# Security Taxonomy

Phase 4.5.1 introduces `SecurityCategory` as a repository-observable capability
taxonomy for future Security Intelligence rules and assessment metadata.

| Category | Serialized value |
| -------- | ---------------- |
| Credential | `security.credential` |
| Secret | `security.secret` |
| Private key | `security.private_key` |
| Certificate | `security.certificate` |
| Configuration | `security.configuration` |
| Transport security | `security.transport_security` |
| Authentication | `security.authentication` |
| Authorization | `security.authorization` |
| Cryptography | `security.cryptography` |
| Repository exposure | `security.repository_exposure` |
| Dependency security | `security.dependency_security` |
| Logging | `security.logging` |
| Session | `security.session` |
| Input validation | `security.input_validation` |
| Miscellaneous | `security.miscellaneous` |
| Unknown | `security.unknown` |

## Non-goals (this phase)

- No OWASP / CWE / CVE / NIST / PCI / SOC 2 mapping
- No rule implementations for these categories
- No compliance scoring

Unknown or unmapped inputs coerce to `security.unknown`.
