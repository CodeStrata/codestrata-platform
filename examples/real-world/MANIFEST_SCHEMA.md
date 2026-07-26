# Showcase Manifest Schema

Manifests are YAML documents under `examples/real-world/manifests/`.

## Required fields

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | string | Stable example ID (`^[a-z][a-z0-9-]{1,62}$`) |
| `name` | string | Human-readable project name |
| `repository_url` | string | HTTPS GitHub URL ending in `.git` or without; only allowlisted hosts |
| `commit_sha` | string | **Full 40-character lowercase hex SHA** (mandatory; never a branch/tag) |
| `license_spdx` | string | SPDX identifier (e.g. `Apache-2.0`, `MIT`) |
| `attribution_url` | string | Canonical upstream page for attribution |
| `primary_languages` | string[] | e.g. `[Java]` |
| `frameworks` | string[] | e.g. `[Spring Boot]` |
| `expected_size_category` | enum | `small` \| `medium` \| `large` |
| `supported_capabilities` | string[] | CodeStrata capabilities exercised |
| `recommended_profile` | string | One of `community`, `local`, `enterprise`, `bedrock`, `openai` |
| `required_tools` | string[] | Host tools needed to fetch/assess (e.g. `git`) |
| `fetch_destination` | string | Directory name under `.codestrata-examples/` |
| `runtime_category` | enum | `fast` \| `moderate` \| `slow` |
| `known_limitations` | string[] | Honest gaps / caveats |

## Optional fields

| Field | Type | Notes |
| ----- | ---- | ----- |
| `description` | string | Short summary |
| `owner` | string | Upstream org/user |
| `allow_submodules` | bool | Default `false`; must stay false unless explicitly approved |
| `build_instructions` | string | Documentation only; fetch never runs builds |
| `expected_approx_size_mb` | number | Rough uncompressed working-tree size |
| `pinned_on` | string | ISO date when maintainers pinned the SHA |

## Pinning rules

* Validation and fetch **must** use `commit_sha` only.
* Floating refs (`main`, `master`, `latest`, tags) are rejected for fetch/checkout.
* Maintainers refresh pins intentionally (see `examples/real-world/README.md`).
