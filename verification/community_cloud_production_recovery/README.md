# Slice 17.10 — Community Cloud production recovery validation

Operations-only verification that production recovery posture is ready:

- Lambda image/config rollback readiness
- Infrastructure rollback with destructive plan gate
- State and lock recovery (read-only simulation accepted)
- Insights/Docs Cloudflare rollback readiness
- Data Lake and remote-state never automatically destroyed
- Final zero-drift required
- Resource recovery classification register

## Run

```bash
PYTHONPATH=. python -m verification.community_cloud_production_recovery
```

Report: `.codestrata-artifacts/validation/suites/sv17-10/community-cloud-production-recovery-verification.json`

## Gates

- `start_slice_17_10=true`
- `start_slice_17_11=false`
- Destructive plans (destroy/replace) blocked; in-place update allowed
- No redesign, commit, tag, or publish
