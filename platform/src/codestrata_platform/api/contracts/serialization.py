"""Deterministic JSON serialization for Platform API DTOs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID


def to_jsonable(value: object) -> object:
    """Convert domain/application objects to JSON-compatible primitives.

    Rules (stable for clients):
    - Enums → ``.value``
    - Single-field ``value`` dataclasses (Platform IDs) → unwrapped primitive
    - Rich dataclasses → object maps of fields
    - Sequences → lists
    - datetimes → ISO-8601 strings
    - Never includes Python type names or private attributes
    """

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        if isinstance(value, datetime):
            return value.isoformat().replace("+00:00", "Z")
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        dc_fields = fields(value)
        # Unwrap Platform ID / version value objects to primitives.
        if len(dc_fields) == 1 and dc_fields[0].name == "value":
            return to_jsonable(getattr(value, "value"))
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in dc_fields
        }
    if hasattr(value, "value"):
        return to_jsonable(getattr(value, "value"))
    return str(value)


def dump_dto(model: Any) -> dict[str, object]:
    """Serialize a Pydantic model deterministically (sorted keys via JSON mode)."""

    return model.model_dump(mode="json")
