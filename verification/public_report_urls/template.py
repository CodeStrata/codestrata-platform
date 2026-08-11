"""Release validation evidence for public report URLs (Epic 19 prep).

Authoritative runtime writer:
  engine/src/codestrata/community_cloud/public_report_url_manifest.py

Default path (gitignored artifacts):
  .codestrata-artifacts/validation/suites/release-v0.2.0/public-report-urls.json

Schema: public-report-urls-manifest:1.1

This template is tracked so Epic 19 corpus validation has a known empty shape.
Do NOT list published reports on reports.codestrata.ai — opaque URL possession only.
"""

from __future__ import annotations

SCHEMA = "public-report-urls-manifest:1.1"

EMPTY_MANIFEST = {
    "schema": SCHEMA,
    "purpose": "Release Epic validation evidence — not production state",
    "assessments": [],
    "engineering_intelligence": [],
    "note": (
        "Populate during final 22-repository corpus: assess → publish → "
        "GET verify HTTP 200 + matching opaque id → append entry. "
        "Founder reviews each reports.codestrata.ai/r/<id> URL manually."
    ),
}

ALLOWED_PUBLIC_HOST_PREFIX = "https://reports.codestrata.ai/r/"

FORBIDDEN_URL_FRAGMENTS = (
    "amazonaws.com",
    "X-Amz-",
    "Authorization",
    "sig=",
    "AWSAccessKeyId",
    "secretsmanager",
)
