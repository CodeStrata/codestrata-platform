"""Bucket-policy encryption deny posture (Slice 8.11 / 8.12).

v0.2.0 decision: NO broad DenyUnencryptedObjectUploads (or equivalent) bucket
policy for encryption headers. Defense in depth is bucket default encryption
+ explicit PutObject ``ServerSideEncryption=AES256`` headers from the Platform
adapter. Absence of a Deny-unencrypted statement is intentional and documented
— not a defect.

Slice 8.12 adds a separate ``DenyInsecureTransport`` bucket policy (TLS only).
That resource must not be confused with an encryption-header deny.
"""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _module_blob() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf"))


def test_bucket_policy_exists_for_secure_transport_only() -> None:
    blob = _module_blob()
    assert 'resource "aws_s3_bucket_policy" "community_data_lake"' in blob
    assert "DenyInsecureTransport" in blob


def test_no_deny_unencrypted_object_uploads_statement() -> None:
    blob = _module_blob()
    assert "DenyUnencryptedObjectUploads" not in blob
    assert "DenyIncorrectEncryptionHeader" not in blob
    assert "x-amz-server-side-encryption" not in blob.lower()


def test_absence_of_deny_unencrypted_is_documented_as_ok() -> None:
    """Documented limitation — bucket default + Put headers only."""

    # This assertion encodes the product decision: we deliberately do not add
    # a broad Deny for missing encryption headers in this slice.
    assert "DenyUnencryptedObjectUploads" not in _module_blob()
