# Repository-Sensitive Evidence

Phase **4.5.2** — reusable repository-visible security-relevant evidence.

This is **platform evidence**, not a Security Intelligence capability package.

## Ownership

| Concern | Owner |
| ------- | ----- |
| Sensitive artifact discovery & content signatures | **Repository-Sensitive Evidence** |
| Security-relevant configuration literals | **Repository-Sensitive Evidence** |
| Redaction / placeholder classification | **Repository-Sensitive Evidence** |
| Vulnerability / severity / remediation | Security Intelligence (future rules) |
| Secret validity / entropy / CVE / SAST | Explicitly out of scope |

Collectors must **not** import `codestrata.domain.security` and must **not** emit
Findings.

Future consumers may include Security, Compliance, Cloud, Configuration, or
Repository Intelligence capabilities.

## Configuration

```toml
[evidence.repository_sensitive]
enabled = false
```

Disabled by default. Independent of `[rules.security]` and
`[assessment.sections.security]`.

## Artifact

`repository-sensitive-evidence.json`

| Field | Value |
| ----- | ----- |
| Schema name | `repository-sensitive-evidence` |
| Schema version | `1.1.0` |
| Artifact schema id | `codestrata.repository_sensitive_evidence` |

### Schema 1.1.0 additive fields

Configuration facts now include typed rule-facing properties:

- `key_family` (credential, secret, tls_verification, hostname_verification,
  authentication, cors_origin, debug, other, unknown)
- `literal_boolean` (normalized when value is boolean)
- `is_wildcard_origin` (explicit `*` for CORS origin keys)

These fields enable Security hygiene rules without re-parsing values.

## Bundle contents

- artifact evidence
- configuration facts (redacted literals)
- coverage
- diagnostics (never Findings)
- limitations
- deterministic fingerprint

## Artifact taxonomy (selected)

Kinds: `private_key`, `public_certificate`, `keystore`, `truststore`,
`environment_file`, `cloud_credentials_file`,
`package_registry_credentials_file`, `ssh_private_key`,
`credential_configuration`, `unknown_sensitive_artifact`.

Discovery bases: exact filename, filename pattern, extension, content
signature, structured content, repository metadata.

Inspection statuses: inspected, metadata_only, unsupported_binary,
skipped_size_limit, malformed, failed.

Content classifications: private_key_material, public_certificate_material,
credential_entries, placeholder_only, no_supported_sensitive_signature,
unknown.

A candidate **filename does not imply** sensitive content. Classification
requires inspected structural signatures.

## Content signatures

Bounded structural markers only (PEM/OpenSSH private keys, PEM certificates,
known credential-section / env assignment patterns). No decoding, trust
validation, entropy scoring, or arbitrary long-string secret classification.

Binary keystores (JKS/P12/PFX/keystore/truststore): metadata only.

## Configuration facts

Supported formats: `.properties`, YAML, JSON, TOML, dotenv-style.

Collect only security-relevant literal keys/values (password/secret/token/TLS/
debug/CORS/auth families, plaintext `http://` endpoints). Never serialize
complete credential values — only redacted preview, fingerprint, length,
value-kind, and placeholder status.

## Placeholder classification

Recognizes empty values, deterministic placeholders (`changeme`, `example`,
…), and environment interpolation (`${VAR}`, `$VAR`). Does not judge
acceptability.

## Coverage / diagnostics / limitations

Coverage counters describe inspected candidates only and do **not** claim a
full-repository security scan.

Diagnostics cover malformed/unsupported/oversized/unreadable cases.
Limitations document snapshot-only scope, no git history, no validity checks,
no keystore decryption, no vulnerability interpretation, and related bounds.

## Explicit deferred scope

Security rules, Findings, severity, assessment inventory, synthesis, CTO
report integration, entropy detection, git history scanning, credential
validity, certificate trust/expiry, keystore decryption, CVEs, CWE/OWASP,
compliance, SAST/DAST, CLI/MCP commands.
