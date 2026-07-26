# Dependency Evidence Ownership

| Concern | Owner | Status |
| ------- | ----- | ------ |
| Manifest / lockfile discovery | Dependency Evidence | 4.4.2 (manifests; not lockfile resolution) |
| Parsing Maven / Gradle / Python manifests | Dependency Evidence | 4.4.2 |
| Normalized coordinates, versions, declared kinds | Dependency Evidence | 4.4.2 |
| Engineering-role taxonomy | Dependency Intelligence | Foundation (4.4.1) |
| Dependency hygiene SharedRules / Findings | Dependency Intelligence | 4.4.3 |
| Dependency assessment section / inventory / synthesis | Dependency Intelligence | Inventory 4.4.4; synthesis 4.4.5; report later |
| Vulnerability / advisory interpretation | Security Intelligence | Not started |
| License policy interpretation | Future | Not started |

Dependency Intelligence **must not** own manifest parsing. Security may later
consume the same Dependency Evidence for vulnerability interpretation.

No CVE feeds, license databases, version-freshness signals, or package-registry /
network calls are introduced in 4.4.2. npm/`package.json` is deferred.
