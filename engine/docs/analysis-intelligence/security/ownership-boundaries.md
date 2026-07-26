# Security Ownership Boundaries

## Principle

> Security Intelligence consumes reusable platform evidence and does not own
> repository parsing or generic evidence truth.

## Ownership matrix

| Concern | Owner |
| ------- | ----- |
| Manifest / lockfile parsing | Dependency Evidence (and future build/container evidence) |
| Potentially sensitive artifacts & config literals | Repository-Sensitive Evidence (`evidence.repository_sensitive`) |
| Source / language facts | Language evidence platforms |
| Shared Finding identity | Shared Finding model |
| Security interpretation / future rules | Security Intelligence |
| CVE / registry / SAST engines | Deferred external integrations (not Security Evidence ownership) |
| CTO report presentation | Future report adapter (not 4.5.x) |

## Explicitly not owned by Security Intelligence

- Generic capability-owned `SecurityEvidence` abstraction (not introduced)
- Owning repository parsers as Security-only truth
- Package registry or vulnerability database access
- Report JSON/HTML customer presentation
- CLI or MCP security commands

Phase 4.5.2 collectors live under platform evidence and must not import Security
domain models or emit Findings.

## Shared Finding

`RuleCategory.SECURITY` → `FindingCategory.SECURITY`.

No parallel `SecurityFinding` or `SecurityIntelligencePack` types.
