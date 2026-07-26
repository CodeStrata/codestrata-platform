# Complexity Evidence (Phase 4.3.2)

Deterministic structural complexity facts for future Technical Debt rules.

## Ownership

| Concern | Owner |
| ------- | ----- |
| Parsing / metric extraction | Language Evidence Platform |
| Debt interpretation (rules + assess) | Technical Debt Intelligence |
| Architecture Intelligence | Unchanged; does not invoke collectors |

## Configuration

```toml
[evidence.complexity]
enabled = true

[evidence.complexity.python]
enabled = true

[evidence.complexity.java]
enabled = true

[evidence.complexity.php]
enabled = true
```

## Support matrix

| Metric | Python | Java | PHP | JS/TS |
| ------ | ------ | ---- | --- | ----- |
| Physical lines (file / callable / type) | yes | yes | yes | no |
| Parameter count | yes | yes | yes | no |
| Branch-point count | yes | yes | yes | no |
| Max nesting depth | yes | yes | yes | no |
| Callable count per class/module | yes | yes | yes | no |
| Cognitive complexity | no | no | no | no |

## Limitations

- Java/PHP lambdas and PHP closures are not extracted as callables.
- Branch points are structural keyword/operator counts, not a certified
  cyclomatic-complexity product metric.
- Generated, vendor, build, and `.codestrata` workspace paths are excluded by default.
- Python method/constructor parameter counts exclude implicit `self` / `cls`.
- PHP uses the same brace-aware structural scan pattern as Java (Phase 5.17.1).
- C# uses the same brace-aware structural scan pattern as Java (Phase 5.18).
- Collectors are invoked by Technical Debt assess orchestration (4.3.4) when
  the TD pack and complexity gates are enabled; Architecture assessment does
  not register them.
