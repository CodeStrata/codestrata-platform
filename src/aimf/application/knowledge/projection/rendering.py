"""Deterministic text rendering helpers for knowledge documents."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any


def stable_json_block(payload: Any, *, heading: str | None = None) -> str:
    """Render a JSON block with sorted keys for byte-stable document content."""

    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
    if heading:
        return f"## {heading}\n\n```json\n{text}\n```\n"
    return f"```json\n{text}\n```\n"


def section(heading: str, body: str) -> str:
    compact = body.strip()
    if not compact:
        return f"## {heading}\n\n_(empty)_\n"
    return f"## {heading}\n\n{compact}\n"


def join_sections(parts: Sequence[str]) -> str:
    return "\n".join(part.rstrip() for part in parts if part and part.strip()) + "\n"


def dump_model(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {str(key): dump_model(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [dump_model(item) for item in value]
    if isinstance(value, (str, int, float, bool)):
        return value
    # Plain test doubles / namespaces: expose public attributes.
    if hasattr(value, "__dict__"):
        return {
            key: dump_model(item)
            for key, item in sorted(vars(value).items())
            if not key.startswith("_")
        }
    return str(value)


def render_finding_content(finding: Any) -> str:
    evidence_rows = []
    for item in getattr(finding, "evidence", ()) or ():
        evidence_rows.append(
            {
                "evidence_type": getattr(item, "evidence_type", None),
                "source_id": getattr(item, "source_id", None),
                "path": getattr(item, "path", None),
                "excerpt": getattr(item, "excerpt", None),
                "node_id": str(getattr(item, "node_id", "") or "") or None,
            }
        )
    parts = [
        f"# Finding: {finding.title}",
        section("Summary", str(finding.description)),
        section(
            "Attributes",
            "\n".join(
                [
                    f"- rule_id: `{finding.rule_id}`",
                    f"- severity: `{finding.severity}`",
                    f"- category: `{finding.category}`",
                    f"- finding_id: `{finding.id}`",
                    f"- confidence: `{confidence_display(finding)}`",
                ]
            ),
        ),
        stable_json_block(evidence_rows, heading="Evidence References"),
        stable_json_block(getattr(finding, "metadata", {}) or {}, heading="Metadata"),
    ]
    return join_sections(parts)


def confidence_display(finding: Any) -> str:
    metadata = getattr(finding, "metadata", None) or {}
    value = metadata.get("confidence") if isinstance(metadata, Mapping) else None
    return str(value) if value is not None else "unknown"


def render_recommendation_content(recommendation: Any) -> str:
    actions = [
        {
            "order": action.order,
            "title": action.title,
            "description": action.description,
            "command": action.command,
            "documentation_ref": action.documentation_ref,
        }
        for action in getattr(recommendation, "actions", ()) or ()
    ]
    evidence_rows = [
        {
            "evidence_type": item.evidence_type,
            "source_id": item.source_id,
            "path": item.path,
            "excerpt": item.excerpt,
        }
        for item in getattr(recommendation, "evidence", ()) or ()
    ]
    parts = [
        f"# Recommendation: {recommendation.title}",
        section("Summary", str(recommendation.summary)),
        section("Rationale", str(recommendation.rationale)),
        section(
            "Attributes",
            "\n".join(
                [
                    f"- recommendation_id: `{recommendation.id}`",
                    f"- priority: `{recommendation.priority}`",
                    f"- category: `{recommendation.category}`",
                    f"- provider_id: `{recommendation.provider_id}`",
                    f"- related_finding_ids: `{', '.join(recommendation.related_finding_ids)}`",
                ]
            ),
        ),
        stable_json_block(actions, heading="Actions"),
        stable_json_block(evidence_rows, heading="Evidence References"),
    ]
    return join_sections(parts)


def render_assessment_content(*, assessment_type: str, section_obj: Any) -> str:
    """Assessment-aware document body with stable section headings for chunking."""

    status = getattr(section_obj, "status", None)
    posture = (
        getattr(section_obj, "overall_posture_summary", None)
        or getattr(section_obj, "executive_summary", None)
        or ""
    )
    synthesis = getattr(section_obj, "synthesis", None)
    themes = (
        getattr(synthesis, "themes", None)
        if synthesis is not None
        else getattr(section_obj, "themes", ())
    )
    conclusions = (
        getattr(synthesis, "conclusions", None)
        if synthesis is not None
        else getattr(section_obj, "conclusions", ())
    )
    recommendations = (
        getattr(synthesis, "recommendations", None)
        if synthesis is not None
        else getattr(section_obj, "recommendations", ())
    )
    if synthesis is not None and not posture:
        posture = getattr(synthesis, "overall_posture_summary", None) or getattr(
            synthesis, "summary", ""
        )

    inventory_payload = {
        "coverage": dump_model(getattr(section_obj, "coverage", None)),
        "execution_summary": dump_model(getattr(section_obj, "execution_summary", None)),
        "finding_ids": list(getattr(section_obj, "finding_ids", ()) or ()),
        "family_inventory": dump_model(
            getattr(section_obj, "performance_family_inventory", None)
            or getattr(section_obj, "capability_family_inventory", None)
            or getattr(section_obj, "family_inventory", None)
            or getattr(section_obj, "signal_family_inventory", None)
        ),
    }
    limitations = dump_model(getattr(section_obj, "limitations", ()) or ())
    diagnostics = dump_model(getattr(section_obj, "diagnostics", ()) or ())

    parts = [
        f"# Assessment: {assessment_type}",
        section(
            "Posture Summary",
            f"status: `{status}`\n\n{posture or '_(no posture summary)_'}",
        ),
        stable_json_block(dump_model(themes) or [], heading="Themes"),
        stable_json_block(dump_model(conclusions) or [], heading="Conclusions"),
        stable_json_block(dump_model(recommendations) or [], heading="Recommendations"),
        stable_json_block(inventory_payload, heading="Inventories"),
        stable_json_block(
            {"limitations": limitations, "diagnostics": diagnostics},
            heading="Limitations and Diagnostics",
        ),
        stable_json_block(
            {
                "section_id": getattr(section_obj, "section_id", None),
                "schema_name": getattr(section_obj, "schema_name", None),
                "section_version": getattr(section_obj, "section_version", None),
                "assessment_id": getattr(section_obj, "assessment_id", None),
                "pack_id": getattr(section_obj, "performance_pack_id", None)
                or getattr(section_obj, "pack_id", None)
                or getattr(section_obj, "architecture_pack_id", None)
                or getattr(section_obj, "security_pack_id", None)
                or getattr(section_obj, "testing_pack_id", None)
                or getattr(section_obj, "cloud_pack_id", None)
                or getattr(section_obj, "ai_readiness_pack_id", None)
                or getattr(section_obj, "dependency_pack_id", None)
                or getattr(section_obj, "technical_debt_pack_id", None),
                "pack_version": getattr(section_obj, "performance_pack_version", None)
                or getattr(section_obj, "pack_version", None),
            },
            heading="Trace Envelope",
        ),
    ]
    return join_sections(parts)


def render_report_section_content(*, section_key: str, section_obj: Any) -> str:
    title = getattr(section_obj, "title", None) or section_key
    executive = getattr(section_obj, "executive_summary", None) or ""
    posture = getattr(section_obj, "overall_posture_summary", None) or ""
    parts = [
        f"# Report Section: {title}",
        section("Posture Summary", f"{posture}\n\n{executive}".strip() or "_(empty)_"),
        stable_json_block(dump_model(getattr(section_obj, "themes", ()) or ()), heading="Themes"),
        stable_json_block(
            dump_model(getattr(section_obj, "conclusions", ()) or ()),
            heading="Conclusions",
        ),
        stable_json_block(
            dump_model(getattr(section_obj, "recommendations", ()) or ()),
            heading="Recommendations",
        ),
        stable_json_block(
            dump_model(getattr(section_obj, "inventory_summary", None)),
            heading="Inventories",
        ),
        stable_json_block(
            {
                "limitations": dump_model(getattr(section_obj, "limitations", ()) or ()),
                "diagnostics": dump_model(getattr(section_obj, "diagnostics", ()) or ()),
            },
            heading="Limitations and Diagnostics",
        ),
        stable_json_block(
            {
                "section_id": getattr(section_obj, "section_id", None),
                "section_version": getattr(section_obj, "section_version", None),
                "schema_name": getattr(section_obj, "schema_name", None),
                "status": getattr(section_obj, "status", None),
                "repository_name": getattr(section_obj, "repository_name", None),
            },
            heading="Heading Hierarchy",
        ),
    ]
    return join_sections(parts)


def render_evidence_content(*, evidence_id: str, evidence_obj: Any) -> str:
    payload = dump_model(evidence_obj)
    parts = [
        f"# Evidence: {evidence_id}",
        stable_json_block(payload, heading="Evidence Summary"),
    ]
    return join_sections(parts)
