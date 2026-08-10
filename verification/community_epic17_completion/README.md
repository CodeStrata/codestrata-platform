# Community Epic 17 Completion Verification (Slice 17.27)

Closure / verification only. No product features. No Transparency Documentation
Epic. No Release Readiness Epic. No publish/tag/corpus.

## Policy

`community-epic17-completion-policy:1.0`

## Schema

`community-epic17-completion-verification:1.0.0`

## Suite

`sv17-27` → `.codestrata-artifacts/validation/suites/sv17-27/`

## Run

```bash
.venv/bin/python -m verification.community_epic17_completion
.venv/bin/python -m pytest tests/verification/community_epic17_completion -q
```

Requires prior live probe cache and tofu zero-drift evidence under the suite
directory (produced during Slice 17.27 verification).
