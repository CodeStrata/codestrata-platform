# Knowledge Graph workspace examples

`codestrata enterprise init <dir>` creates a minimal starter workspace with:

- `enterprise.yaml`
- empty typed directories (organizations, applications, repositories, …)
- one starter organization manifest

Add YAML manifests under those directories, then:

```bash
codestrata enterprise validate <dir>
codestrata enterprise build <dir>
```

Do not rely on fictional packaged domain workspaces. Tests use temporary
inline fixtures instead of checked-in sample enterprises.
