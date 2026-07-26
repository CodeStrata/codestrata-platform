# Examples

Plan providers for a repository:

```bash
codestrata evidence plan --repository . --json
```

Inspect Python provider metadata:

```bash
codestrata evidence providers inspect language.python.core --json
```

Enable the pipeline only when intentionally validating equivalence:

```toml
[evidence.language]
enabled = true
```
