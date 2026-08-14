# Marketplace publication guide — CodeStrata – Engineering Assessment

**Role:** Publishing and packaging checklist only.  
**Authoritative Marketplace listing copy:** [`README.md`](README.md)

Do **not** maintain a second divergent product listing here. Branding visuals
are covered by [`docs/marketplace-branding.md`](docs/marketplace-branding.md).
Listing narrative is covered by
[`docs/marketplace-documentation.md`](docs/marketplace-documentation.md).

**Status:** Live Visual Studio Marketplace listing
https://marketplace.visualstudio.com/items?itemName=CodeStrataAI.codestrata-assessment
(`CodeStrataAI.codestrata-assessment` **0.2.2**). Community Engine/CLI remains v0.2.1.

Active Community editor extension: **VS Code only**.

## Extension identifier (stable)

| Extension | Identifier | displayName |
| --------- | ---------- | ----------- |
| VS Code | `CodeStrataAI.codestrata-assessment` | CodeStrata – Engineering Assessment |

Publisher ID: **`CodeStrataAI`** (existing Visual Studio Marketplace publisher;
the VSIX manifest `publisher` field must match this ID exactly). Do not rename
after release without explicit approval.

## Classification

| Extension | Status |
| --------- | ------ |
| codestrata-assessment | **FREEZE CANDIDATE** — package **0.2.2** (Marketplace live listing still **0.2.1** until publish) |

Do **not** treat a later local VSIX rebuild as an unpublished listing overwrite.
Marketplace versions are monotonic.

## Branding assets

Authoritative brand masters: `design-system/assets/brand/`  
Marketplace packaging derivatives: `vscode-plugin/media/`  
Generator: `vscode-plugin/scripts/generate_marketplace_visuals.py`  
Historical amber-era sources (archive only): `governance/assets/extension-branding/`

- Packaged icon: `media/codestrata-icon.png` (128×128)
- Marketplace gallery screenshots: five Community journey images under `media/`
- Optional banner art: `media/marketplace-banner.png`
- Screenshots: gallery order documented in branding docs and `README.md`

## Secrets (never in git)

| Secret | Storage |
| ------ | ------- |
| Azure DevOps PAT (Marketplace) | OS keychain / CI secret `VSCE_PAT` |
| Open VSX token | OS keychain / CI secret `OVSX_TOKEN` |

```bash
# Create Azure DevOps PAT with Marketplace (Publish) scope — do not commit.
# https://code.visualstudio.com/api/working-with-extensions/publishing-extension

export VSCE_PAT='…'          # local shell only
export OVSX_TOKEN='…'        # local shell only
```

## Visual Studio Marketplace

### One-time publisher setup

1. Open https://marketplace.visualstudio.com/manage
2. Use existing publisher ID **`CodeStrataAI`** (display name: CodeStrata)
3. Optionally verify domain ownership for the verified badge
4. Create Azure DevOps PAT with **Marketplace → Publish**

### Manual VSIX upload

1. `cd vscode-plugin && npm test && npm run package`
   (`package` uses `--allow-missing-repository --no-rewrite-relative-links`
   because extension source is private; do not point listing URLs at a
   private GitHub source repository.)
2. Upload `codestrata-assessment-0.2.2.vsix` in Marketplace manage → Update
   (Marketplace already published 0.2.1; listing versions are monotonic)
3. Confirm README renders (listing source is `README.md`)
4. Attach screenshots from `media/screenshot-*.png` if the upload UI requires them
5. Review → Make Public only after human approval

### Automated publish

```bash
cd vscode-plugin
npm test
npm run package
npx --yes @vscode/vsce publish --packagePath ./codestrata-assessment-0.2.2.vsix -p "$VSCE_PAT"
# Prefer: vsce login CodeStrataAI   then   vsce publish
```

Dry-run (validates package; does not upload when unsupported):

```bash
npx --yes @vscode/vsce ls --no-dependencies
npx --yes @vscode/vsce package --no-dependencies
```

## Open VSX

1. Eclipse account + Publisher Agreement: https://open-vsx.org/
2. Create / claim namespace **`codestrata`**
3. Generate access token → store as `OVSX_TOKEN` only

```bash
npx ovsx publish codestrata-assessment-0.2.2.vsix -p "$OVSX_TOKEN"
```

Clean install/update validation: [docs/clean-install-update.md](docs/clean-install-update.md).

## Release gates (must all pass)

- [ ] `npm test` (vscode-plugin)
- [ ] `npm run package` produces VSIX containing icon + README
- [ ] Icon 128 PNG present; screenshots synthetic / no secrets (Slice 14.6 visuals)
- [ ] Gallery banner uses Design System canvas (`#f4f6f3` / light)
- [ ] README / CHANGELOG / SECURITY / PRIVACY / SUPPORT / LICENSE present
- [ ] displayName + description accurate; no Platform-only claims
- [ ] Publisher `CodeStrataAI` created and owned
- [ ] Credentials only in approved secret storage
- [ ] Human approval to publish
- [ ] Marketplace visual assets verification PASS (sv14-6) when regenerating media

## Post-publish verification

1. Marketplace / Open VSX pages resolve
2. Fresh VS Code install from marketplace (clean install validation)
3. First command: **Run Assessment**
4. Engine install path works
5. Classify as **VERIFIED_INSTALLABLE**

## Related

- [`README.md`](README.md) — Marketplace listing
- [`docs/marketplace-documentation.md`](docs/marketplace-documentation.md)
- [`docs/marketplace-branding.md`](docs/marketplace-branding.md)
- [`docs/marketplace-visual-assets.md`](docs/marketplace-visual-assets.md)
- `vscode-plugin/RELEASE_CHECKLIST.md`
- `governance/assets/extension-branding/MARKETPLACE_PUBLICATION.md`
