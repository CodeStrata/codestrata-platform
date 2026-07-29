# Real-world showcases

Pinned third-party open-source applications for demonstrating CodeStrata on
realistic codebases **without** vendoring upstream source into this repository.

## Layout

```text
real-world/
├── manifests/           # one YAML per showcase (exact commit SHA required)
├── scripts/
│   ├── fetch_example.py # safe fetch
│   └── run_showcase.py  # fetch + assess + summary
├── MANIFEST_SCHEMA.md
└── THIRD_PARTY.md
```

Fetched trees land under the **examples repository root**:

```text
.codestrata-examples/<fetch_destination>/
```

Generated assessment output:

```text
reports/showcases/<example-id>/
```

Both paths are gitignored. Curated, bounded summaries live in
`expected-results/<example-id>/` for public distribution.

A root `codestrata.toml` in this repository supplies Community Engine settings
so `codestrata assess` and `run_showcase.py` work from a standalone clone.

## Commands

From a **codestrata-examples** checkout:

```bash
python real-world/scripts/fetch_example.py --list
python real-world/scripts/fetch_example.py spring-petclinic
python real-world/scripts/run_showcase.py spring-petclinic
```

Equivalent assess (after fetch):

```bash
codestrata assess \
  --repo .codestrata-examples/spring-petclinic \
  --output reports/showcases/spring-petclinic \
  --profile community \
  --no-ai
```

From the private **codestrata-platform** monorepo, the same portable scripts
live under `examples/real-world/scripts/`. Convenience wrappers also exist at
`scripts/fetch_example.py` and `scripts/run_showcase.py` (they invoke the
portable scripts; the default workspace is still `examples/`).

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
