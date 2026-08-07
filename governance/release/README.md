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

## Epic 12 CI / release boundaries (Slices 12.9–12.10)

- Active editor extension: **VS Code only** (Cursor retired)
- Community vs Infrastructure: separate export targets; Infrastructure is
  `private_infrastructure_only` and independently versioned — not a Community
  release artifact
- Workflow: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
- Verifier (12.9): `python -m verification.ci_release_boundaries`
- Completion (12.10): `python -m verification.product_cleanup_repository_split_completion`
  → `reports/verification/sv12-10/product-cleanup-repository-split-completion-verification.json`
- Ordinary CI does not publish, deploy, tag, plan, apply, or destroy
- Epic 12 complete for v0.2.0 epic scope; Epic 13 not started
