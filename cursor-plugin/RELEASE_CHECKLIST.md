# Community release checklist — CodeStrata Cursor Extension

**Version:** 0.2.0  
**Do not publish** until a human explicitly requests Marketplace publish **and** the
manual Cursor gate below passes.

## Packaging

- [ ] `npm ci`
- [ ] `npm test`
- [ ] `npm run test:host`
- [ ] `npm run package:dry`
- [ ] `npm run package` produces `.vsix`
- [ ] VSIX contents audited (runtime + docs; no tests/src/secrets)
- [ ] package.json metadata complete (displayName, icon, repository, license, engines)
- [ ] CHANGELOG entry for the release version

## Product

- [ ] First-run welcome (Engine ready / missing / incompatible)
- [ ] Guided Engine install
- [ ] Deterministic Engineering Assessment
- [ ] Cursor rule generation / refresh / clear
- [ ] Suggested questions categorized
- [ ] Optional AI remains opt-in
- [ ] No Platform dependency
- [ ] Thin-client architecture preserved

## Compatibility

- [ ] Documented in COMPATIBILITY.md
- [ ] Engine `>=0.1.0 <2.0.0`
- [ ] Report schema `1.2` (major `1.x`)
- [ ] `engines.vscode` `^1.85.0`

---

## Manual Cursor release gate (mandatory before public release)

Validate inside an **actual supported Cursor build**. Do not mark publicly
releasable until this gate passes.

Record: Cursor version · OS · Engine version · report schema · model used ·
repository tested · result · screenshots · deviations.

### Steps

1. Install the packaged VSIX in Cursor.
2. Open a trusted test repository.
3. Confirm extension activation.
4. Confirm commands appear in the Command Palette.
5. Confirm Engine discovery (or Install Engine path).
6. Run a real **Engineering Assessment**.
7. Confirm findings and recommendations load.
8. Confirm `.cursor/rules/codestrata-engineering.mdc` is generated.
9. Open Cursor Chat or Agent.
10. Ask at least five grounded questions (below).
11. Verify answers reference actual assessment findings.
12. Verify unsupported / nonexistent findings get an uncertainty response.
13. Refresh the assessment; verify stale context is replaced.
14. Clear the assessment; verify only the CodeStrata-generated rule is removed.
15. Restart Cursor; confirm state restores safely.
16. Test missing Engine behavior.
17. Test incompatible Engine behavior (if available).
18. Test assessment cancellation.
19. Test multi-root selection.
20. Test an untrusted workspace (Engine/rule write blocked).
21. Open the generated HTML report.
22. Uninstall and reinstall the extension.
23. Confirm uninstall does **not** auto-delete user assessment artifacts or rules
    without explicit Clear Assessment.

### Required grounded questions

- What are the highest-priority findings?
- Which architecture risks should I inspect first?
- Which technical debt should be addressed in the first sprint?
- Explain one actual rule from the assessment.
- What information is missing from the assessment?

### Required negative test

Ask about a finding that does **not** exist. Cursor must not be instructed to
confirm it as fact.

### Gate status

- [ ] **NOT PASSED** until manually completed and recorded
- Live Cursor Chat grounding is **not** claimed by automated `test:host`

---

## Generated rule governance

Recommended default (**Option A**): treat
`.cursor/rules/codestrata-engineering.mdc` as a **local generated artifact** and
add it to `.gitignore` if teams do not want assessment snapshots in git.

Option B: commit intentionally for shared team context.

The extension does **not** silently modify `.gitignore`.
