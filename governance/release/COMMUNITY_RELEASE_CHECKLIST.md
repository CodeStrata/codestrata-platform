# Community Release Checklist

**Status:** Normative  
**Authority:** Release engineering  
**Orchestrator:** `python scripts/validate_release.py`

This checklist is for **public Community distribution** readiness. It does not
publish remotes, upload marketplace packages, or perform signing.

## Preflight

- [ ] Clean working tree (`git status`) for the intended release commit
- [ ] Version consistency across Engine package / CLI (`0.1.x` train)
- [ ] Extension versions intentional (may differ from Engine)
- [ ] Schema versions **not** forced to match product versions
- [ ] `public-export-manifest.yaml` reviewed (authoritative allowlist)
- [ ] No customer-specific rule packs or proprietary docs staged for export

## Validation (automated)

Run:

```bash
python scripts/validate_release.py
# optional packaging:
python scripts/validate_release.py --with-build
# optional full monorepo gates:
python scripts/validate_release.py --with-security-check --with-verify-release
```

Confirm artifacts under `.generated/release-artifacts/` (gitignored):

- [ ] `release-surface-inventory.json`
- [ ] `version-consistency.json`
- [ ] `dependency-inventory.json`
- [ ] `export-secret-scan.json` (0 blocking findings)
- [ ] `sbom-*.cdx.json` + `sbom-combined.cdx.json`
- [ ] `SHA256SUMS` (verified)
- [ ] `release-provenance.json`
- [ ] `public-export-manifest.yaml` copy

## Export / extraction

- [ ] `python scripts/export-public-repos.py` (or via validate_release)
- [ ] `python scripts/validate-public-exports.py --skip-install`
- [ ] Staging repos under `.export-staging/` contain `.codestrata-export-snapshot.json`
- [ ] Re-export is content-idempotent (no unexpected drift)
- [ ] Platform / governance / knowledge / `.env` absent from staging
- [ ] Synthetic test knowledge not exported

## Package / build (when releasing Engine)

- [ ] `python -m build` produces sdist + wheel
- [ ] Wheel contents inspected (no platform/, no `.env`)
- [ ] Clean venv install: `codestrata --help`, `codestrata ai --help`
- [ ] Non-AI sample assessment succeeds
- [ ] HTML + JSON reports validate

## Extensions

- [ ] `npm ci` / `npm test` / `npm run package` (or dry-run) clean
- [ ] Packaged VSIX inspected (license, README, icon, no internal config)
- [ ] Lockfiles present (`package-lock.json`)

## Legal / security docs

- [ ] LICENSE / NOTICE present where required
- [ ] SECURITY.md present (Engine + extensions + docs)
- [ ] CONTRIBUTING / CODE_OF_CONDUCT / SUPPORT as required by each repo
- [ ] Package metadata license matches MIT (approved project license)
- [ ] No internal legal drafts published

## Integrity / provenance

- [ ] SHA-256 checksums generated and verified
- [ ] Provenance lists commit hash, tooling version, artifact hashes
- [ ] No personal filesystem paths or credentials in provenance
- [ ] Signing noted as `not_configured` (future-ready)

## Publication readiness (manual; out of band)

- [ ] Release notes drafted
- [ ] GitHub mirror destinations confirmed
- [ ] Marketplace assets ready (extensions)
- [ ] Maintainer approval recorded

## References

- [`public-export-manifest.yaml`](../../public-export-manifest.yaml)
- [`scripts/validate_release.py`](../../scripts/validate_release.py)
- [`scripts/verify_release.py`](../../scripts/verify_release.py)
- [`RELEASE_SURFACE_INVENTORY.md`](RELEASE_SURFACE_INVENTORY.md)
- Engine policy: [`../../engine/SECURITY.md`](../../engine/SECURITY.md)
