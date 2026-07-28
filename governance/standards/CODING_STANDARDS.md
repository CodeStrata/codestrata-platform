# Coding Standards

**Status:** Foundation  
**Authority:** Standards

## Objective

Define how CodeStrata Engine and Platform code should be written and reviewed.

## Scope

Python packages under `engine/` and `platform/`. Does not replace Ruff/mypy
configuration in-repo.

## 1. Tooling (authoritative today)

| Tool | Role | Location |
| ---- | ---- | -------- |
| Ruff | Lint | Repo config / `verify_release` |
| mypy | Types (`engine/src` gate) | `verify_release` |
| pytest | Tests | `-m "not network"` default gate |

<!-- TODO: Document Platform mypy policy when the release gate expands. -->

## 2. Style principles

1. Match surrounding code; avoid drive-by refactors.
2. Prefer explicit types on public APIs.
3. Keep modules focused; avoid god services growing without phase approval.
4. No speculative abstractions.
5. Prefer focused modules under `engine/src/codestrata/` and
   `platform/src/codestrata_platform/` mirroring existing packages.
6. Keep deterministic analysis authoritative; AI must not invent findings
   ([007_AI_PHILOSOPHY.md](../constitution/007_AI_PHILOSOPHY.md)).
7. Do not commit secrets or generated report trees.

## 3. Error handling

- Use domain/application errors intentionally.
- Sanitize exception messages at trust boundaries
  (see [005_SECURITY_PRIVACY_PRINCIPLES.md](../constitution/005_SECURITY_PRIVACY_PRINCIPLES.md)).

## 4. Comments & docs in code

- Comment *why*, not *what*.
- Do not leave stale TODOs without an owner/phase marker.

## 5. References

- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [engine/CONTRIBUTING.md](../../engine/CONTRIBUTING.md)
- [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md)
- [TESTING_STANDARDS.md](TESTING_STANDARDS.md)
