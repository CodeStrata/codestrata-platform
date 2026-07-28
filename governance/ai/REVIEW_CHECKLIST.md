# AI Change Review Checklist

**Status:** Foundation  
**Authority:** AI guidance

## Objective

Checklist for reviewing AI-produced (or human) diffs before merge.

## Scope

PR / local review. Complements [INTERNAL_RELEASE_CHECKLIST.md](../playbooks/INTERNAL_RELEASE_CHECKLIST.md).

## Architecture

- [ ] Dependency direction preserved (Engine ↛ Platform)
- [ ] No layer bypass (API → Application → Domain/Infrastructure as designed)
- [ ] No new persistence or API surface unless phase requires it

## Security & privacy

- [ ] No secrets in code, tests, logs, or docs
- [ ] Errors sanitized at boundaries
- [ ] Tenant isolation unchanged

## Product / branding

- [ ] Uses **CodeStrata** / **CodeStrata Engine** / **CodeStrata Platform** correctly
- [ ] AI not treated as product name
- [ ] Terminology matches [NAMING_CONVENTIONS.md](../standards/NAMING_CONVENTIONS.md)
- [ ] Visual / UI changes follow [`../assets/DESIGN-SYSTEM.md`](../assets/DESIGN-SYSTEM.md)

## Quality

- [ ] Focused tests added for the change
- [ ] Ruff clean on touched paths
- [ ] Relevant pytest green
- [ ] No unrelated refactors

## Docs

- [ ] Engineering docs updated only if technically incorrect
- [ ] No duplicated Governance content

<!-- TODO: Add checklist items for report HTML and OpenAPI once PE standards freeze. -->

## References

- [005_SECURITY_PRIVACY_PRINCIPLES.md](../constitution/005_SECURITY_PRIVACY_PRINCIPLES.md)
- [003_ARCHITECTURE_PRINCIPLES.md](../constitution/003_ARCHITECTURE_PRINCIPLES.md)
