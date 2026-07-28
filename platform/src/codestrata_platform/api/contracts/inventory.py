"""Build a machine-readable Platform API contract inventory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterator

from fastapi import FastAPI
from fastapi.routing import APIRoute

from codestrata_platform.api.contracts import API_MAJOR_VERSION, VERSION_POLICY

# Docs / OpenAPI projections — not public business contracts.
_INTERNAL_DOC_PATHS = {
    "/api/docs",
    "/api/openapi.json",
    "/api/openapi.yaml",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/docs/oauth2-redirect",
}


def _response_model_name(response_model: object | None) -> str | None:
    if response_model is None:
        return None
    origin = getattr(response_model, "__origin__", None)
    args = getattr(response_model, "__args__", None)
    if origin is list and args:
        inner = _response_model_name(args[0]) or str(args[0])
        return f"list[{inner}]"
    name = getattr(response_model, "__name__", None)
    if isinstance(name, str) and name and name != "list":
        return name
    # Generics such as PageResponse[T]
    text = str(response_model)
    if text.startswith("typing.") or "ForwardRef" in text:
        return name
    if "[" in text:
        return text.replace("codestrata_platform.api.", "").replace(
            "portfolio.dto.", ""
        ).replace("portfolio.aggregation_dto.", "")
    return name or text


def _classification(path: str, methods: set[str], response_model: object | None) -> str:
    if path in _INTERNAL_DOC_PATHS or path.startswith("/api/docs/"):
        return "internal"
    if "archive" in path and "post" in methods:
        return "internal"
    if path in {"/health", "/ready"}:
        return "stable"
    if response_model is None:
        return "partial"
    return "stable"


def _iter_api_routes(app: FastAPI) -> Iterator[tuple[str, APIRoute]]:
    """Yield ``(full_path, route)`` across FastAPI 0.140 nested routers."""

    for route in app.routes:
        if isinstance(route, APIRoute):
            yield route.path, route
            continue
        if type(route).__name__ != "_IncludedRouter":
            continue
        yield from _walk_included(route)


def _walk_included(included: Any, parent_prefix: str = "") -> Iterator[tuple[str, APIRoute]]:
    ctx = getattr(included, "include_context", None)
    ctx_prefix = getattr(ctx, "prefix", "") or ""
    # Prefer include-context prefix when present; otherwise keep parent.
    base = ctx_prefix or parent_prefix
    router = included.original_router
    for item in router.routes:
        if isinstance(item, APIRoute):
            yield f"{base}{item.path}", item
        elif type(item).__name__ == "_IncludedRouter":
            yield from _walk_included(item, parent_prefix=base)


def build_contract_inventory(app: FastAPI) -> dict[str, Any]:
    operations: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for path, route in _iter_api_routes(app):
        methods = {method.lower() for method in (route.methods or set())}
        for method in sorted(route.methods or []):
            if method.upper() in {"HEAD", "OPTIONS"}:
                continue
            key = (method.upper(), path)
            if key in seen:
                continue
            seen.add(key)
            classification = _classification(path, methods, route.response_model)
            operations.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "name": route.name,
                    "classification": classification,
                    "response_model": _response_model_name(route.response_model),
                    "tags": list(route.tags or []),
                }
            )

    summary = {
        "stable": sum(1 for item in operations if item["classification"] == "stable"),
        "partial": sum(1 for item in operations if item["classification"] == "partial"),
        "internal": sum(1 for item in operations if item["classification"] == "internal"),
        "deprecated": sum(
            1 for item in operations if item["classification"] == "deprecated"
        ),
        "total": len(operations),
    }
    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
        "api_major": API_MAJOR_VERSION,
        "version_policy": VERSION_POLICY,
        "summary": summary,
        "operations": sorted(
            operations, key=lambda item: (item["path"], item["method"])
        ),
    }
