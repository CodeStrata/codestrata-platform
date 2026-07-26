# Security Hygiene Rules

Phase **4.5.3** — `security.core` @ **1.0.0**

Rules consume **only** in-memory `AggregatedRepositorySensitiveEvidence`.
They do not re-read files, reparse configuration, or invent vulnerability
conclusions.

## Configuration

```toml
[evidence.repository_sensitive]
enabled = true

[rules]
enabled = true

[rules.security]
enabled = true

[assessment.sections.security]
enabled = true
```

All gates default to **disabled**. Rules never trigger evidence collection.

## Rule catalog

| Rule ID | Trigger | Severity | Category |
| ------- | ------- | -------- | -------- |
| `security.private-key-material` | Inspected artifact with `private_key_material` | HIGH | PRIVATE_KEY |
| `security.credential-literal` | Credential/secret key + non-empty literal | HIGH | CREDENTIAL |
| `security.placeholder-credential` | Credential/secret key + recognized placeholder | LOW | CREDENTIAL |
| `security.tls-verification-disabled` | Typed TLS verification control disabled | HIGH | TRANSPORT_SECURITY |
| `security.hostname-verification-disabled` | Typed hostname verification disabled | HIGH | TRANSPORT_SECURITY |
| `security.authentication-disabled` | Typed authentication control disabled | HIGH | AUTHENTICATION |
| `security.permissive-cors-origin` | Typed CORS origin is explicit `*` | MEDIUM | CONFIGURATION |
| `security.debug-enabled` | Typed debug control enabled (all source roles) | MEDIUM | CONFIGURATION |

Confidence is **HIGH** for all listed rules.

## Exclusions

- Filename-only candidates without signatures
- Public certificates (not private keys)
- Binary keystores (metadata-only)
- Environment references and empty values for credential-literal
- Missing / malformed / unsupported evidence facts
- Evidence diagnostics (never become Findings)

## Source-role behavior

Rules preserve source role on Findings. Debug findings are emitted for all
roles (production/test/unknown). Assessment inventory separation is deferred.

## Finding identity

Finding IDs use `finding:{rule_id}:{digest}` from stable subject keys
(rule id, evidence id, path, key/role). **Value fingerprints are not** part of
the Finding ID — the ID identifies the repository condition, not secret material.

## Redaction

Findings may include redacted previews and fingerprints. Complete credential or
private-key content is never serialized.

## Assessment schema

`security-assessment` **1.2.0** — additive inventories, hotspots, diagnostics
summary, and production-primary finding views (Phase 4.5.4). Hygiene Findings
and pack behavior from 4.5.3 are unchanged.
No inventories, hotspots, themes, conclusions, recommendations, or report
integration.

## Deferred rules

- plaintext HTTP endpoint hygiene
- source-code secret regex / entropy
- certificate expiry/trust
- keystore inspection
- dependency CVE reinterpretation
- SAST / data-flow / injection analysis
