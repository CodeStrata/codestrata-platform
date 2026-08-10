# Slice 17.25 — Community Status GitHub authority + workflow cleanup verification

Verifies GitHub-published release authority for public Community Status
(`engine_version`, stars, repository identity), workflow authority register
hygiene, export-source repository guards, and absence of root deploy workflows.
Optional live probe: `GET https://api.codestrata.ai/api/v1/community/status`.

## Run

```bash
PYTHONPATH=engine/src:platform/src:. .venv/bin/python -m verification.community_status_workflow_cleanup
```

Report: `.codestrata-artifacts/validation/suites/sv17-25/community-status-workflow-cleanup-verification.json`

## Tests

```bash
PYTHONPATH=engine/src:platform/src:. .venv/bin/pytest tests/verification/community_status_workflow_cleanup/ -q
```

## Soft limitations (PASS_WITH_LIMITATIONS)

- `worktree_uncommitted`
- `monorepo_pre_cutover_authority`
- `live_platform_push_deferred`
- `package_github_release_mismatch` (e.g. live `0.1.0` vs package `0.2.0`)
- `github_v0_2_0_release_not_published`
- `status_api_deploy_pending` (live API unreachable)
- `github_temporary_unavailable_handled`

## Hard fail

- `start_slice_17_26=true` in policy
- Fabricated hardcoded GitHub stars in service code
- GH PAT or static AWS keys embedded in workflow files
