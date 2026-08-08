# Slice 16.3 — Repository Code Cleanup

Evidence-required removal of obsolete/dead/duplicate source code.

## Authority

- Policy: `repository-code-cleanup-policy:1.0`
- Schema: `repository-code-cleanup-verification:1.0.0`
- Report: `reports/verification/sv16-3/repository-code-cleanup-verification.json`

## Run

```bash
python -m verification.repository_code_cleanup
```

Does not clean assets (16.4), dependencies (16.5), generated storage (16.6), or split repos (16.7).
No commit/tag/publish/deploy.
