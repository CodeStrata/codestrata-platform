# Testing Standards

**Status:** Foundation  
**Authority:** Standards

## Objective

Define how CodeStrata tests are organized, named, and gated.

## Scope

`engine/tests/`, `platform/tests/`, `tests/architecture/`.

## 1. Principles

1. Prefer focused regression tests for each hardening / phase change.
2. Mark network-dependent tests with `network` (excluded from default gate).
3. Architecture boundary tests are mandatory for Engine ↔ Platform rules.
4. Do not skip tests without a documented reason.

## 2. Layers

| Layer | Examples |
| ----- | -------- |
| Unit / application | Domain rules, services with memory fakes |
| API | FastAPI TestClient contracts |
| Persistence | PostgreSQL / memory adapters |
| Architecture | Import direction, package boundaries |
| Dogfood | End-to-end product path (non-network where possible) |

## 3. Fixtures

- Prefer explicit local fixtures over shared global state.
- Do not imply unsupported databases (Platform = PostgreSQL).

## 4. Release gate

Default: `pytest -m "not network"` via `scripts/verify_release.py`.

## 5. References

- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [DOGFOOD_CHECKLIST.md](../playbooks/DOGFOOD_CHECKLIST.md)
- [tests/architecture/](../../tests/architecture/)
