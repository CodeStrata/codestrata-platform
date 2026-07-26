# CLI

```bash
codestrata enterprise init [dir] [--force]
codestrata enterprise validate [dir] [--json] [--strict]
codestrata enterprise build [dir] [--json]
codestrata enterprise inspect [entity-id] [--depth N] [--json]
codestrata enterprise query applications|repositories|impact|ownership|dependencies ...
codestrata enterprise explain <relationship-id>
codestrata enterprise compare <left-graph-id> <right-graph-id>
```

Thin adapters only; workflow lives in `EnterpriseKnowledgeService`.
