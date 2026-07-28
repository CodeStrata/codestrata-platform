# Release Candidate (RC) Checklist

**Status:** Foundation  
**Authority:** Playbook

## Objective

Gate an engineering Release Candidate (e.g. Platform RC1) without public publish.

## Scope

Internal engineering milestone. Does **not** create git tags or publish packages
unless a later phase explicitly requires it.

## Checklist

- [ ] Architecture complete for the declared milestone
- [ ] PostgreSQL production path ready (Platform)
- [ ] SQLite status resolved and documented (Platform vs Engine knowledge store)
- [ ] APIs stable; OpenAPI complete for exposed routes
- [ ] Migrations clean
- [ ] Security / reliability / performance / observability hardening intact
- [ ] End-to-end dogfood passed
- [ ] Feature flags intentional
- [ ] Dependency graph clean (no speculative unused deps)
- [ ] `verify_release` passed

## Declaration

When all items pass, declare the engineering RC name (example:
**CodeStrata Platform RC1**) in the phase deliverable only — do not tag unless asked.

## References

- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- [DOGFOOD_CHECKLIST.md](DOGFOOD_CHECKLIST.md)
- [002_ENGINEERING_CONSTITUTION.md](../constitution/002_ENGINEERING_CONSTITUTION.md)
