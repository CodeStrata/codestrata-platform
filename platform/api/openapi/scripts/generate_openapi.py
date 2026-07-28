#!/usr/bin/env python3
"""Generate the canonical Platform OpenAPI tree from the live FastAPI app.

Canonical location: platform/api/openapi/

Workflow:
  1. Controllers / DTOs remain the implementation surface for now.
  2. This script exports OpenAPI 3.1, annotates maturity extensions, and writes
     the modular + bundled artifacts that Swagger UI and contract tests use.
  3. Contract tests fail if live routes drift from the checked-in OpenAPI.

Does not deploy. Does not publish. Internal engineering only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
OPENAPI_ROOT = Path(__file__).resolve().parents[1]
PARTIAL_OPS = {
    ("get", "/api/v1/engineering/technologies"),
    ("get", "/api/v1/engineering/findings"),
    ("get", "/api/v1/engineering/recommendations"),
    ("get", "/api/v1/engineering/metrics"),
    ("get", "/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/technologies"),
    ("get", "/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/findings"),
    ("get", "/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/recommendations"),
    ("get", "/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/risks"),
    ("get", "/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/modernization"),
    ("get", "/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/coverage"),
    ("get", "/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/repository-profiles"),
    ("get", "/api/v1/portfolio-snapshots/{portfolio_snapshot_id}/overview"),
}
INTERNAL_OPS = {
    ("post", "/api/v1/portfolios/{portfolio_id}/archive"),
}
TAG_OWNERS = {
    "Health": "platform-api",
    "Organizations": "platform-tenancy",
    "Workspaces": "platform-tenancy",
    "Repositories": "platform-tenancy",
    "Assessments": "platform-assessments",
    "Assessment Intelligence": "platform-assessments",
    "Ingestion": "platform-ingestion",
    "Ingestion Artifacts": "platform-ingestion",
    "Ingestion Intelligence": "platform-ingestion",
    "Engineering Intelligence": "platform-engineering",
    "Knowledge Graphs": "platform-knowledge-graph",
    "Knowledge Graph Intelligence": "platform-knowledge-graph",
    "Retrieval": "platform-retrieval",
    "Answering": "platform-answering",
    "Portfolio": "platform-portfolio",
    "Portfolio Retrieval": "platform-portfolio",
    "Portfolio Answering": "platform-portfolio",
    "Executive Intelligence": "platform-executive",
    "Executive Presentation": "platform-executive",
    "Strategic Portfolio Roadmap": "platform-executive",
}


def _slug(path: str) -> str:
    cleaned = path.strip("/").replace("{", "").replace("}", "")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", cleaned).strip("-").lower()
    return cleaned or "root"


def _annotate(schema: dict[str, Any]) -> dict[str, Any]:
    schema["openapi"] = "3.1.0"
    info = schema.setdefault("info", {})
    info["title"] = "CodeStrata Platform API"
    info["version"] = info.get("version") or "v1"
    info["x-codestrata-audience"] = "internal"
    info["x-codestrata-hostname"] = "https://platform.codestrata.ai"
    info["description"] = (
        (info.get("description") or "")
        + "\n\n"
        + "## Internal contract foundation\n\n"
        + "This specification is the **canonical** Platform API contract "
        + "(OpenAPI 3.1). Swagger UI at `/api/docs` is a generated projection.\n\n"
        + "Audience: internal engineers only. Not for public docs, Community "
        + "export, sitemap, or search indexing.\n\n"
        + "Hostname (internal): `https://platform.codestrata.ai` — API base "
        + "`https://platform.codestrata.ai/api`.\n"
    )
    schema["servers"] = [
        {
            "url": "https://platform.codestrata.ai",
            "description": "Internal Platform hostname (API under /api/v1)",
        },
        {
            "url": "http://127.0.0.1:8000",
            "description": "Local development (uvicorn) when enabled",
        },
    ]
    schema["x-codestrata-contract"] = {
        "canonical": "platform/api/openapi/openapi.yaml",
        "swagger_projection": "/api/docs",
        "openapi_yaml": "/api/openapi.yaml",
        "openapi_json": "/api/openapi.json",
        "audience": "internal",
        "public_export": False,
        "community_schema_reuse": {
            "assessment_report": (
                "engine/schemas/assessment/codestrata.io/v1.2/"
                "AssessmentReport.json"
            ),
            "policy": "Extend Community contracts; do not duplicate them.",
        },
        "versioning": {
            "url_prefix": "/api/v1",
            "breaking_change": "New major path (/api/v2)",
            "within_major": "Additive only; clients ignore unknown fields",
            "deprecation": "Announce in release notes; retain ≥1 minor cycle",
        },
        "error_model": {
            "implemented": "ErrorResponseDto",
            "preferred_future": "RFC 9457 Problem Details (proposed mapping)",
        },
        "authentication": {
            "implemented": "PlatformApiKey (HTTP Bearer shared secret)",
            "proposed": ["JWT", "SSO / OIDC", "Internal service identity"],
        },
    }

    # Reusable common schemas (canonical copies also live under schemas/).
    components = schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas.setdefault(
        "ProblemDetails",
        {
            "type": "object",
            "description": (
                "RFC 9457 Problem Details (PROPOSED mapping alongside "
                "ErrorResponseDto). Not yet the runtime envelope."
            ),
            "properties": {
                "type": {"type": "string", "format": "uri"},
                "title": {"type": "string"},
                "status": {"type": "integer"},
                "detail": {"type": "string"},
                "instance": {"type": "string", "format": "uri"},
                "code": {"type": "string"},
            },
            "required": ["type", "title", "status"],
            "x-codestrata-status": "proposed",
        },
    )
    schemas.setdefault(
        "OpaqueId",
        {
            "type": "string",
            "description": "Opaque Platform identifier (organization, workspace, …)",
            "minLength": 1,
            "x-codestrata-status": "implemented",
        },
    )
    schemas.setdefault(
        "IsoTimestamp",
        {
            "type": "string",
            "format": "date-time",
            "description": "ISO-8601 timestamp",
            "x-codestrata-status": "implemented",
        },
    )
    schemas.setdefault(
        "WarningItem",
        {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["code", "message"],
            "x-codestrata-status": "implemented",
        },
    )
    schemas.setdefault(
        "JobStatus",
        {
            "type": "string",
            "enum": ["queued", "running", "succeeded", "failed", "cancelled"],
            "description": "Async job status vocabulary (shared)",
            "x-codestrata-status": "implemented",
        },
    )

    # Proposed security schemes (not enabled at runtime).
    schemes = components.setdefault("securitySchemes", {})
    schemes.setdefault(
        "PlatformJwt",
        {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "PROPOSED user/session JWT. Not implemented.",
            "x-codestrata-status": "proposed",
        },
    )
    schemes.setdefault(
        "PlatformOidc",
        {
            "type": "oauth2",
            "description": "PROPOSED SSO / OIDC. Not implemented.",
            "x-codestrata-status": "proposed",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://platform.codestrata.ai/oauth/authorize",
                    "tokenUrl": "https://platform.codestrata.ai/oauth/token",
                    "scopes": {
                        "platform.read": "Read Platform resources",
                        "platform.write": "Mutate Platform resources",
                    },
                }
            },
        },
    )

    for path, methods in schema.get("paths", {}).items():
        for method, operation in list(methods.items()):
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            key = (method, path)
            if key in INTERNAL_OPS:
                status = "internal"
            elif key in PARTIAL_OPS:
                status = "partial"
            else:
                status = "implemented"
            tags = operation.get("tags") or []
            owner = "platform-api"
            for tag in tags:
                if tag in TAG_OWNERS:
                    owner = TAG_OWNERS[tag]
                    break
            operation["x-codestrata-status"] = status
            operation["x-codestrata-owner"] = owner
            operation["x-codestrata-audience"] = "internal"
            if not operation.get("operationId"):
                op_id = f"{method}_{_slug(path)}".replace("-", "_")
                operation["operationId"] = op_id
    return schema


def _write_yaml(path: Path, data: Any) -> None:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("PyYAML required") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _split_modular(schema: dict[str, Any]) -> None:
    """Write modular path/schema fragments for maintainability."""

    paths_dir = OPENAPI_ROOT / "paths"
    schemas_dir = OPENAPI_ROOT / "schemas"
    responses_dir = OPENAPI_ROOT / "responses"
    parameters_dir = OPENAPI_ROOT / "parameters"
    examples_dir = OPENAPI_ROOT / "examples"
    for directory in (paths_dir, schemas_dir, responses_dir, parameters_dir, examples_dir):
        directory.mkdir(parents=True, exist_ok=True)

    by_tag: dict[str, dict[str, Any]] = defaultdict(dict)
    for path, methods in schema.get("paths", {}).items():
        tags: set[str] = set()
        for method, operation in methods.items():
            if method in {"get", "post", "put", "patch", "delete"} and isinstance(
                operation, dict
            ):
                tags.update(operation.get("tags") or ["Untagged"])
        tag = sorted(tags)[0] if tags else "Untagged"
        by_tag[tag][path] = methods

    for tag, paths in sorted(by_tag.items()):
        _write_yaml(paths_dir / f"{_slug(tag)}.yaml", {"paths": paths})

    components = schema.get("components") or {}
    for name, value in sorted((components.get("schemas") or {}).items()):
        _write_yaml(schemas_dir / f"{name}.yaml", {name: value})

    _write_yaml(
        responses_dir / "error.yaml",
        {
            "Unauthorized": {
                "description": "Missing or invalid Platform API key",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponseDto"}
                    }
                },
            },
            "ProblemDetailsProposed": {
                "description": "PROPOSED RFC 9457 problem response",
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/ProblemDetails"}
                    }
                },
            },
        },
    )
    _write_yaml(
        parameters_dir / "common.yaml",
        {
            "Page": {
                "name": "page",
                "in": "query",
                "schema": {"type": "integer", "minimum": 1, "default": 1},
            },
            "Size": {
                "name": "size",
                "in": "query",
                "schema": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
            },
            "Sort": {
                "name": "sort",
                "in": "query",
                "schema": {"type": "string"},
            },
        },
    )
    _write_yaml(
        examples_dir / "auth.yaml",
        {
            "bearerApiKey": {
                "summary": "Platform API key (not an AI provider token)",
                "value": {"Authorization": "Bearer ${CODESTRATA_PLATFORM_API_KEY}"},
            }
        },
    )

    # Bundled root — single file Swagger + contract tests consume.
    _write_yaml(OPENAPI_ROOT / "openapi.yaml", schema)
    (OPENAPI_ROOT / "openapi.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    inventory = {
        "operations": 0,
        "by_status": defaultdict(int),
        "by_tag": defaultdict(int),
        "paths": len(schema.get("paths") or {}),
    }
    for path, methods in schema.get("paths", {}).items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            inventory["operations"] += 1
            inventory["by_status"][operation.get("x-codestrata-status", "unknown")] += 1
            for tag in operation.get("tags") or ["Untagged"]:
                inventory["by_tag"][tag] += 1
    inventory["by_status"] = dict(inventory["by_status"])
    inventory["by_tag"] = dict(inventory["by_tag"])
    (OPENAPI_ROOT / "inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if checked-in openapi.json differs from regenerated output",
    )
    args = parser.parse_args(argv)

    sys.path.insert(0, str(ROOT / "platform" / "src"))
    sys.path.insert(0, str(ROOT / "engine" / "src"))
    from codestrata_platform.api.app import create_app

    app = create_app(use_memory=True)
    schema = _annotate(app.openapi())

    if args.check:
        existing = OPENAPI_ROOT / "openapi.json"
        if not existing.is_file():
            print("missing openapi.json — run without --check first", file=sys.stderr)
            return 1
        current = json.loads(existing.read_text(encoding="utf-8"))
        # Compare path+method+status annotations (stable contract core).
        def fingerprint(doc: dict[str, Any]) -> set[tuple[str, str, str]]:
            rows: set[tuple[str, str, str]] = set()
            for path, methods in (doc.get("paths") or {}).items():
                for method, operation in methods.items():
                    if method not in {"get", "post", "put", "patch", "delete"}:
                        continue
                    if not isinstance(operation, dict):
                        continue
                    rows.add(
                        (
                            method,
                            path,
                            str(operation.get("x-codestrata-status", "")),
                        )
                    )
            return rows

        if fingerprint(current) != fingerprint(schema):
            print(
                "OpenAPI drift detected. Run: "
                "python platform/api/openapi/scripts/generate_openapi.py",
                file=sys.stderr,
            )
            return 1
        print("OpenAPI contract fingerprint OK")
        return 0

    _split_modular(schema)
    print(f"Wrote {OPENAPI_ROOT / 'openapi.yaml'}")
    print(f"Wrote {OPENAPI_ROOT / 'openapi.json'}")
    print(f"Wrote modular fragments under {OPENAPI_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
