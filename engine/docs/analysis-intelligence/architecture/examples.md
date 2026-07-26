# Architecture Examples

## Unit selection

```text
codestrata.application.rules.architecture  →  codestrata.application
com.example.domain.model             →  com.example.domain
com.example.hub                      →  com.example.hub   (reverse-DNS depth ≥ 3)
```

## Cycle after collapse

Nested `codestrata.ai.agents` ↔ `codestrata.ai.providers` collapses into `codestrata.ai` and does
not produce a self-loop finding. Cross-module cycles such as
`codestrata.application` ↔ `codestrata.infrastructure` remain reportable.

## Coupling

Only comparable architectural modules are scored. `codestrata.cli` (composition root)
is excluded. Absolute threshold and peer-relative floor must both be met.

## Enable assess merge

```toml
[rules]
enabled = true

[rules.architecture]
enabled = true
```

```bash
codestrata rules list --category architecture
codestrata rules inspect architecture.dependency-cycle
codestrata assess
```
