# community-22-repository-validation (Slice 17.13)

Community 22-repository release-validation suite scaffolding under `.codestrata-artifacts/`.

## Run (offline scaffolding)

```bash
.venv/bin/python -m verification.community_22_repository_validation
```

Dry-run (skip clone/assess execution):

```bash
.venv/bin/python -m verification.community_22_repository_validation --skip-execute
```

Report:

`.codestrata-artifacts/validation/suites/sv17-13/community-22-repository-validation-verification.json`

Suite manifest:

`.codestrata-artifacts/validation/suites/sv17-13/manifest.json`

Slice 17.14 is not started. Full 22-repository assessment execution is not part of scaffolding.
