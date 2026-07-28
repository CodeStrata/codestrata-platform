# Platform API Version Policy

## Current major

`v1` — URL prefix `/api/v1`

## Compatibility rules

| Change type | Allowed in `v1`? | Guidance |
| --- | --- | --- |
| Add optional response field | Yes | Clients must ignore unknown fields |
| Add optional request field with default | Yes | |
| Add new endpoint | Yes | |
| Remove/rename field | No | Requires `/api/v2` |
| Change field type / enum meaning | No | Requires `/api/v2` |
| Change error envelope keys | No | Requires major bump |

## Client expectations

- Send `Authorization: Bearer <platform-api-key>` when configured
- Treat `error.code` as the stable machine key
- Prefer `X-Correlation-Id` for support tickets
- Do not depend on undocumented dict shapes

## Header

`X-CodeStrata-API-Version` echoes the URL major version.
