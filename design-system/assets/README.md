# Design System assets

Authoritative home for CodeStrata product visual assets (Slice 14.10).

```text
assets/
└── brand/     # master mark, master wordmark, approved variants
```

`brand/` is generated and verified by `scripts/generate_brand_assets.py`; run it
with `--check` to detect drift. Lineage, consumers, and copy authorization are
recorded in `design-system/contracts/assets.json`, and the rules live in
`design-system/documentation/brand-assets.md`.

Consumer-specific copies stay where packaging requires them (documentation site,
Platform API portal, Engine report package, VS Code media) because those
repositories are exported independently. Those copies must remain byte-identical
to their master; verification enforces it.

`governance/assets/` is the historical amber-era archive and is not authoritative.
