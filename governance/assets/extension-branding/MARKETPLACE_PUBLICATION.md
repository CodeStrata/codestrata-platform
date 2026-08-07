# Marketplace publication — CodeStrata – Engineering Intelligence

**Status:** Preparation complete · **Do not publish** until release gates pass and a
human explicitly requests publish with stored credentials.

Active Community editor extension (Slice 12.2): **VS Code only**.
The former Cursor extension product and its packaging surfaces were removed
(Slices 12.1–12.2). Broad documentation/branding cleanup is deferred to Slice 12.3.

## Extension identifier (stable)

| Extension | Identifier | displayName |
| --------- | ---------- | ----------- |
| VS Code | `codestrata.codestrata-vscode` | CodeStrata – Engineering Intelligence |

Publisher namespace: **`codestrata`** (create/claim before first publish; do not
rename after release without explicit approval).

As of 2026-07-28, no published `codestrata.*` CodeStrata extensions were found on
the Visual Studio Marketplace (name collisions with unrelated “Codex*” products
are different publishers).

## Classification

| Extension | Status |
| --------- | ------ |
| codestrata-vscode | **MARKETPLACE_READY** (packaged + gates documented; not published) |

The extension is not **PUBLISHED** or **VERIFIED_INSTALLABLE** from a marketplace
until live install is confirmed after publish.

Do **not** treat local VSIX presence as Marketplace publication.

Publisher namespace `codestrata` must be created/claimed on Visual Studio
Marketplace and Open VSX before first upload. Prefer public repository URLs under
`github.com/CodeStrata/*` when org repos exist — do not rename extension IDs after
publish.

## Branding assets

Canonical sources: `governance/assets/extension-branding/`

- Icon PNG sizes 16–512 + SVG tile
- Marketplace banner 1280×640
- Packaged icon: `vscode-plugin/media/codestrata-icon.png` (128×128)

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
2. Create publisher ID **`codestrata`** (Name: CodeStrata)
3. Optionally verify domain ownership for the verified badge
4. Create Azure DevOps PAT with **Marketplace → Publish**

### Manual VSIX upload

1. `cd vscode-plugin && npm test && npm run package`
2. Upload `codestrata-vscode-0.2.0.vsix` in Marketplace manage → New extension
3. Attach screenshots from `media/screenshot-*.png`
4. Review README rendering → Make Public

### Automated publish

```bash
cd vscode-plugin
npm test
npm run package
npx --yes @vscode/vsce publish --packagePath ./codestrata-vscode-0.2.0.vsix -p "$VSCE_PAT"
# Prefer: vsce login codestrata   then   vsce publish
```

Dry-run (no upload when unsupported by CLI version — still validates package):

```bash
npx --yes @vscode/vsce ls --no-dependencies
npx --yes @vscode/vsce package --no-dependencies
```

## Open VSX

1. Eclipse account + Publisher Agreement: https://open-vsx.org/
2. Create / claim namespace **`codestrata`**
3. Generate access token → store as `OVSX_TOKEN` only

```bash
npx ovsx publish codestrata-vscode-0.2.0.vsix -p "$OVSX_TOKEN"
```

Open VSX improves VSCodium and other open-editor discovery. Treat Open VSX as
required for broad open-editor reach alongside Visual Studio Marketplace.

## Release gates (must all pass)

- [ ] `npm test` (vscode-plugin)
- [ ] `npm run package` produces VSIX containing icon **and** screenshots (for README rendering)
- [ ] Icon 128 PNG present; screenshots synthetic / no secrets
- [ ] README / CHANGELOG / SECURITY / PRIVACY / SUPPORT / LICENSE present
- [ ] README covers purpose, audience, Engine dependency, first command, supported
      Engine/schema versions, privacy/security, troubleshooting, support, docs link,
      and Community vs Platform boundary (no Platform-only feature claims)
- [ ] displayName + description accurate
- [ ] Publisher `codestrata` created and owned
- [ ] Credentials only in approved secret storage (`VSCE_PAT` / `OVSX_TOKEN`)
- [ ] Human approval to publish

## Why publish may remain deferred

1. Do not publish until all release gates pass.
2. Publisher ownership / PATs must be configured in approved secret storage.
3. Human approval is required for the first public listing.

## Post-publish verification

1. Marketplace / Open VSX pages resolve
2. Fresh VS Code install from marketplace
3. First command: **Run Assessment**
4. Engine install path works
5. Classify as **VERIFIED_INSTALLABLE**

## Related

- `vscode-plugin/RELEASE_CHECKLIST.md`
- `vscode-plugin/MARKETPLACE.md`
