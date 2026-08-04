"""Unsafe-metadata classification helpers (never echo rejected values)."""

from __future__ import annotations

import re
from typing import Any

from codestrata_platform.intelligence_reporting.application.errors import (
    UnsafeAssessmentMetadataError,
)
from codestrata_platform.intelligence_reporting.application.validation import (
    validate_report_document,
)

# Shape-only classifiers — do not capture or return matched secret text.
_DASHED_BEGIN = re.compile(r"-----BEGIN", re.IGNORECASE)
_FULL_PEM = re.compile(
    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----[\s\S]*?"
    r"-----END (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
    re.IGNORECASE,
)
_HEADER_ONLY = re.compile(
    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
    re.IGNORECASE,
)


def classify_description_shape(description: str) -> str:
    """Return a safe classification label for a Finding description."""

    if _FULL_PEM.search(description):
        return "private_key_body_or_full_pem"
    if _HEADER_ONLY.search(description) or _DASHED_BEGIN.search(description):
        return "pem_header_marker_in_description"
    return "no_pem_shape"


def find_unsafe_customer_field_paths(document: dict[str, Any]) -> list[str]:
    """Return JSON paths that fail Platform safety (no values)."""

    try:
        validate_report_document(document)
    except UnsafeAssessmentMetadataError as exc:
        # Message format: "$.path must not contain ..."
        message = str(exc)
        path = message.split(" must ", 1)[0].strip()
        return [path] if path.startswith("$") else ["$"]
    return []


# Safe descriptive phrases that must be accepted by Platform validation when
# used as Finding descriptions (no embedded secret values).
SAFE_DESCRIPTIVE_PHRASES: tuple[str, ...] = (
    "Hardcoded credential detected in repository configuration.",
    "Password placeholder observed; rotate credentials if exposed.",
    "Secret-like configuration should use a secrets manager.",
    "Credential rotation recommended after private-key material findings.",
    "Value redacted. Sensitive credential material was detected.",
    "Intentionally vulnerable demonstration repository contributed security findings.",
    "Sensitive private-key material signature detected; value redacted.",
)

# Deliberately unsafe fixtures — values are synthetic test tokens only.
# Deliberately unsafe fixtures — shapes Platform validate_report_document rejects.
# (Bearer/ghp/connection-string shapes are covered by Engine redaction tests;
# Platform's customer-field gate focuses on assignment and PEM/AKIA markers.)
UNSAFE_FIXTURE_DESCRIPTIONS: tuple[str, ...] = (
    "password=SuperSecretPass999",
    "AKIAIOSFODNN7EXAMPLE",
    "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0Z3VS5JJcds3xfn=\n-----END RSA PRIVATE KEY-----",
    "api_key=sk-live-abcdefghijklmnopqrstuvwxyz012345",
    "secret=raw-credential-value-xyz",
    "password=hunter2-secret-raw",
    "-----BEGIN PRIVATE KEY-----",
    "nested metadata with -----BEGIN EC PRIVATE KEY----- marker",
)
