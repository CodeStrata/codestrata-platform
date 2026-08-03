"""Reusable strict request primitives for future Community Cloud events."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, Field, StrictBool, StrictInt, StrictStr
from pydantic.types import StringConstraints

from codestrata_platform.community_cloud_api.validation.sanitization import (
    contains_secret_like_value,
    is_safe_repository_relative_path,
    reject_control_characters,
)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_CLIENT_NAME_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_VERSION_RE = re.compile(r"^[A-Za-z0-9._+-]+$")
_METADATA_KEY_RE = re.compile(r"^[A-Za-z0-9._:-]+$")


def _reject_controls(value: str) -> str:
    if reject_control_characters(value):
        raise ValueError("unsafe_value")
    return value


def _reject_secret_like(value: str) -> str:
    if contains_secret_like_value(value):
        raise ValueError("unsafe_value")
    return value


def _require_identifier(value: str) -> str:
    value = _reject_controls(value)
    if not _IDENTIFIER_RE.fullmatch(value):
        raise ValueError("invalid_format")
    return _reject_secret_like(value)


def _require_client_name(value: str) -> str:
    value = _reject_controls(value)
    if not _CLIENT_NAME_RE.fullmatch(value):
        raise ValueError("invalid_format")
    return _reject_secret_like(value)


def _require_version(value: str) -> str:
    value = _reject_controls(value)
    if not _VERSION_RE.fullmatch(value):
        raise ValueError("invalid_format")
    return value


def _require_metadata_key(value: str) -> str:
    value = _reject_controls(value)
    if not _METADATA_KEY_RE.fullmatch(value):
        raise ValueError("invalid_format")
    return value


def _require_safe_label(value: str) -> str:
    value = _reject_controls(value)
    return _reject_secret_like(value)


def _require_repo_relative_path(value: str) -> str:
    value = _reject_controls(value)
    if not is_safe_repository_relative_path(value):
        raise ValueError("unsafe_value")
    return _reject_secret_like(value)


def _require_event_id(value: str) -> str:
    from codestrata_platform.community_cloud_api.event_identity.validation import (
        validate_event_id_text,
    )

    return validate_event_id_text(value)


def _require_installation_id(value: str) -> str:
    from codestrata_platform.community_cloud_api.event_identity.validation import (
        validate_installation_id_text,
    )

    return validate_installation_id_text(value)


# Protocol identifiers — ASCII conservative character set.
ApiIdentifier = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=128, strict=True),
    AfterValidator(_require_identifier),
]
ApiEventName = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=64, strict=True),
    AfterValidator(_require_identifier),
]
ApiEventId = Annotated[
    StrictStr,
    StringConstraints(min_length=8, max_length=128, strict=True),
    AfterValidator(_require_event_id),
]
ApiInstallationId = Annotated[
    StrictStr,
    StringConstraints(min_length=8, max_length=128, strict=True),
    AfterValidator(_require_installation_id),
]
ApiClientName = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=64, strict=True),
    AfterValidator(_require_client_name),
]
ApiClientVersion = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=32, strict=True),
    AfterValidator(_require_version),
]
ApiSchemaVersion = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=32, strict=True),
    AfterValidator(_require_version),
]
ApiTimestampString = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=64, strict=True),
    AfterValidator(_reject_controls),
]
# Human-readable labels may include Unicode; still reject controls/secrets.
ApiSafeLabel = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=128, strict=True),
    AfterValidator(_require_safe_label),
]
ApiSafeMetadataKey = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=64, strict=True),
    AfterValidator(_require_metadata_key),
]
ApiSafeMetadataValue = Annotated[
    StrictStr,
    StringConstraints(min_length=0, max_length=256, strict=True),
    AfterValidator(_require_safe_label),
]
ApiRepositoryLanguage = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=64, strict=True),
    AfterValidator(_require_identifier),
]
ApiPlatformName = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=64, strict=True),
    AfterValidator(_require_identifier),
]
# Available for later path-bearing fields — not used by production routes yet.
ApiRepositoryRelativePath = Annotated[
    StrictStr,
    StringConstraints(min_length=1, max_length=512, strict=True),
    AfterValidator(_require_repo_relative_path),
]

# Strict scalars — no string↔number↔bool coercion.
ApiStrictInt = Annotated[StrictInt, Field()]
ApiStrictBool = Annotated[StrictBool, Field()]

# Bounded collection helpers (use with Field on model attributes).
DEFAULT_MAX_LIST_ITEMS = 50
DEFAULT_MAX_DICT_ITEMS = 50
