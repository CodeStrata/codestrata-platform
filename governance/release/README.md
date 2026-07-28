# Release Engineering

Community distribution readiness, extraction hardening, and release surfaces.

| Document | Purpose |
| --- | --- |
| [COMMUNITY_RELEASE_CHECKLIST.md](COMMUNITY_RELEASE_CHECKLIST.md) | Repeatable Community public-distribution gate |
| [RELEASE_SURFACE_INVENTORY.md](RELEASE_SURFACE_INVENTORY.md) | Public vs internal surface map |
| [EXTRACTION_HARDENING.md](EXTRACTION_HARDENING.md) | First-time + update extraction |

Authoritative machine manifest (monorepo root):

- [`public-export-manifest.yaml`](../../public-export-manifest.yaml)

Orchestrator:

```bash
python scripts/validate_release.py
python scripts/validate_release.py --with-build
python scripts/validate_release.py --check-idempotent
```

Generated artifacts land under `.generated/release-artifacts/` (gitignored; not
committed under `governance/`).

Related playbooks:

- [`../playbooks/INTERNAL_RELEASE_CHECKLIST.md`](../playbooks/INTERNAL_RELEASE_CHECKLIST.md) (internal train)
- [`../playbooks/RC_CHECKLIST.md`](../playbooks/RC_CHECKLIST.md)
