# Internal Release Checklist

**Status:** Foundation  
**Authority:** Playbook

## Objective

Repeatable checklist before shipping a CodeStrata monorepo release candidate or
internal release train.

## Scope

Engineering release readiness. Not public package publish steps (see maintainer
handbook).

## Pre-release

- [ ] ROADMAP / CHANGELOG notes prepared for the train
- [ ] No unintended secrets in tree
- [ ] Migrations reviewed (Platform PostgreSQL)
- [ ] Feature flags intentional and documented

## Validation

- [ ] `python scripts/verify_release.py` (or `--skip-export` when export N/A)
- [ ] `ruff check .`
- [ ] `mypy engine/src`
- [ ] `pytest -m "not network"`
- [ ] `scripts/security_check.py`
- [ ] Architecture / OpenAPI tests green

## Post-validation

- [ ] RC checklist completed ([RC_CHECKLIST.md](RC_CHECKLIST.md))
- [ ] Dogfood completed ([DOGFOOD_CHECKLIST.md](DOGFOOD_CHECKLIST.md)) when required
- [ ] Tag / publish only with explicit maintainer approval
- [ ] Public contract changes reviewed against
  [PUBLIC_CONTRACT_COMPATIBILITY.md](PUBLIC_CONTRACT_COMPATIBILITY.md)

Community public distribution gate:

- [`../release/COMMUNITY_RELEASE_CHECKLIST.md`](../release/COMMUNITY_RELEASE_CHECKLIST.md)
- Orchestrator: `python scripts/validate_release.py`

## References

- [scripts/verify_release.py](../../scripts/verify_release.py)
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [platform/README.md](../../platform/README.md)
