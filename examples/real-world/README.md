# Real-world showcases

Pinned third-party open-source applications for demonstrating CodeStrata on
realistic codebases **without** vendoring upstream source into the monorepo.

## Layout

```text
real-world/
├── manifests/           # one YAML per showcase (exact commit SHA required)
├── scripts/
│   ├── fetch_example.py # safe fetch (also via scripts/fetch_example.py)
│   └── run_showcase.py  # fetch + assess + summary (scripts/run_showcase.py)
├── MANIFEST_SCHEMA.md
└── THIRD_PARTY.md
```

Fetched trees land under the monorepo root:

```text
.codestrata-examples/<fetch_destination>/
```

Generated assessment output:

```text
reports/showcases/<example-id>/
```

Both paths are gitignored. Curated, bounded summaries live in
`examples/expected-results/<example-id>/` for public distribution.

## Commands

From a **codestrata-examples** checkout (portable):

```bash
python real-world/scripts/fetch_example.py --list
python real-world/scripts/fetch_example.py spring-petclinic
python real-world/scripts/run_showcase.py spring-petclinic
```

From the **codestrata-platform** monorepo (wrappers):

```bash
python scripts/fetch_example.py --list
python scripts/fetch_example.py spring-petclinic
python scripts/run_showcase.py spring-petclinic
```

Equivalent assess (after fetch):

```bash
codestrata assess \
  --repo .codestrata-examples/spring-petclinic \
  --output reports/showcases/spring-petclinic \
  --profile community \
  --no-ai
```

Note: the product profile name is `community` (there is no `balanced` profile).

## Security protections

* Only manifests under `manifests/` are accepted (no arbitrary URLs).
* Exact 40-character commit SHA required; floating refs rejected.
* Destination confined to `.codestrata-examples/`.
* No project install/build execution; no submodule initialization.
* Provenance written as `.codestrata-example-provenance.json` beside the checkout.

## Refreshing pinned revisions

Maintainers intentionally bump `commit_sha` + `pinned_on`, re-run the showcase,
and update curated expected-results and `THIRD_PARTY.md`. Do not automate floating
`main`/`master` pins.

## Optional AI enrichment

Baseline showcases use `--no-ai`. Optional `--with-ai` requires separate provider
credentials and is out of scope for default offline CI.
