# Community release checklist (CodeStrata VS Code Extension)

**Version:** 0.2.0  
**Do not publish** until a human explicitly requests Marketplace publish.

## Packaging

- [ ] `npm install`
- [ ] `npm test`
- [ ] `npm run test:host` (where Extension Host is available)
- [ ] `npm run package` produces `.vsix`
- [ ] `package.json` metadata: displayName, description, publisher, icon, license, repository, homepage, bugs, engines, categories, keywords
- [ ] CHANGELOG entry for the release version

## Product

- [ ] First-run welcome when Engine missing
- [ ] Guided Engine install (uv / pipx / pip)
- [ ] `codestrata version` verification
- [ ] `codestrata doctor` after install
- [ ] Deterministic Engineering Assessment works
- [ ] Findings + HTML report open
- [ ] Optional AI remains opt-in; no secrets in settings
- [ ] No Platform dependency
- [ ] Thin-client architecture preserved

## Compatibility

- [ ] VS Code `^1.85.0`
- [ ] Engine CLI `0.2.x` (release builds; no prerelease)
- [ ] Assessment schema `1.2`

## Marketplace assets

- [ ] Icon 128×128
- [ ] Screenshot(s) under `media/`
- [ ] README marketplace-ready
- [ ] SECURITY / PRIVACY / SUPPORT / CODE_OF_CONDUCT / LICENSE

## Extraction

- [ ] EXTRACTION.md reviewed
- [ ] Public export manifest entry validated


## Marketplace publication gates

- [ ] Publisher `codestrata` created/owned (VS Marketplace + Open VSX namespace)
- [ ] `VSCE_PAT` / `OVSX_TOKEN` in approved secrets storage only
- [ ] `npm run package` VSIX contains `media/codestrata-icon.png`
- [ ] Screenshots reviewed (synthetic, no secrets)
- [ ] README marketplace rendering checked
- [ ] Human approval recorded before `vsce publish` / `ovsx publish`
- [ ] Post-publish install verified → VERIFIED_INSTALLABLE

## Epic / verification gates

- [x] Epic 13 VS Code Extension complete for v0.2.0 epic scope (`sv13-15`)
- [ ] Marketplace published (separate gate)
- [ ] Release tag created (separate gate)
- [ ] Production deploy (separate gate)
- [ ] Epic 14 started (not part of Epic 13)

See [MARKETPLACE.md](MARKETPLACE.md) and `governance/assets/extension-branding/MARKETPLACE_PUBLICATION.md`.
