# Dependency Hygiene Rules (Phase 4.4.3 / 4.4.3A)

Dependency Intelligence hygiene rules consume **Dependency Evidence only**.
They never reparse manifests, execute build tools, or contact registries.

## Rule inventory

| Rule ID | Severity | Confidence | Match contract |
| ------- | -------- | ---------- | -------------- |
| `dependency.unresolved-version` | MEDIUM | HIGH | Version expression **proven unresolved** under a supported local contract |
| `dependency.mutable-version` | MEDIUM | HIGH | Bounded mutable syntax: `*-SNAPSHOT`, `latest`, `latest.release`, `RELEASE`, `+`, `N.+` |
| `dependency.unbounded-requirement` | MEDIUM | HIGH | Python registry-style declaration with no version specifier (extras/markers preserved) |
| `dependency.conflicting-exact-versions` | HIGH | HIGH | Same normalized identity, different exact versions, same narrow overlap context |
| `dependency.duplicate-declaration` | LOW | HIGH | Equivalent repeated declaration in the same context |

## `dependency.unresolved-version` precision (4.4.3A)

Evidence distinguishes:

| Status | Meaning | Finding? |
| ------ | ------- | -------- |
| `resolved` | Supported local contract resolved the expression | No |
| `proven_unresolved` | Supported local contract inspected; expression still unresolved | Yes |
| `unsupported_resolution` | Resolution mechanism not inspected / unsupported | No (diagnostic) |
| `not_applicable` | No version expression / version not required | No |

**Maven:** Missing `${property}` after inspecting local `pom.xml` properties →
`proven_unresolved`. Versionless managed deps and unfetched parent/BOM remain
non-findings (management / unsupported coverage).

**Gradle (minimal contract):** `${…}` / property interpolations are recorded as
`unsupported_version_resolution:gradle_interpolation_uninspected` diagnostics
with partial coverage. They do **not** become findings solely because the
collector did not resolve them. gradle.properties / ext / catalogs are not
inspected in this phase.

## Overlap context (conflicts / duplicates)

Same:

- ecosystem
- manifest path
- declaration kind
- configuration name
- profile / optional group
- environment marker
- source classification
- dependency-management flag
- optional flag (duplicates)

Do **not** flag across modules, profiles, groups, management-vs-active, or
unproven marker exclusivity.

## Mutable syntax (explicit)

Classified as mutable:

- Maven/Gradle `…-SNAPSHOT`
- `latest`, `latest.release`, `RELEASE`
- `+` and prefix wildcards such as `1.+`

**Not** mutable by default: ordinary ranges such as `>=1.0,<2.0`.

## Configuration

```toml
[rules]
enabled = true

[rules.dependency]
enabled = true

[rules.dependency.unresolved_version]
enabled = true

[evidence.dependency]
enabled = true

[assessment.sections.dependency]
enabled = true
```

Pack and evidence gates are independent. Rules enabled without evidence →
`not_applicable` / section `insufficient_evidence`.

## Explicit non-goals

Outdated/latest lookup, CVEs, licenses, transitive conflicts, unused deps,
DependencyRole classification, themes/conclusions/scores, CTO report sections,
npm/`package.json`, Gradle execution, remote parent/BOM resolution.
