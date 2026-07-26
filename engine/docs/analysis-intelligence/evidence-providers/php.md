# PHP language evidence provider

Provider ID: `language.php.core`

Collects PHP source-file, import (`use` / `require` / `include`), architecture
unit/layer, and framework-usage facts using the shared architecture view
builder. Composer package declarations are collected by Dependency Evidence
(`dependency.composer.manifest`), not this provider.

## Related providers

| Provider ID | Role |
| --- | --- |
| `language.php.core` | Architecture / import / framework hits |
| `language.php.complexity` | Structural complexity (brace-scan; Phase 5.17.1) |
| `dependency.composer.manifest` | Composer declared dependencies |

## Applicability

Applicable when repository paths include at least one `.php` source file.

## Supported frameworks (detection / framework hits)

- Laravel (`Illuminate\\`)
- Symfony (`Symfony\\Component`, `Symfony\\Bundle`)
- Doctrine ORM
- CodeIgniter
- Laminas

## Complexity (Phase 5.17.1)

PHP complexity uses the same shared `File` / `Type` / `Callable` evidence models
as Java/Python. Extraction is a brace-aware structural scan (not a full PHP AST
and not a certified cyclomatic product metric). Traits map to the existing
`CLASS` type kind.

Enable via:

```toml
[evidence.complexity]
enabled = true

[evidence.complexity.php]
enabled = true

[rules.technical_debt]
enabled = true
```

## Dependency hygiene (Phase 5.17.1)

The Dependency Intelligence pack includes `php` in `supported_languages`.
Composer declarations participate in shared hygiene rules (duplicates, mutable
`dev-*` branches, unbounded `*`). Ordinary Composer ranges such as `^11.0` are
not classified as mutable.

```toml
[evidence.dependency]
enabled = true

[evidence.dependency.composer]
enabled = true

[rules.dependency]
enabled = true
```

## Limitations

- No full PHP AST; regex-based imports and brace-scan complexity only
- Vendor trees are ignored by default
- Type-only dependency capability is unsupported for PHP
- Closures / anonymous functions are not extracted for complexity
- Composer `^` / `~` ranges are intentional constraints, not mutable findings
