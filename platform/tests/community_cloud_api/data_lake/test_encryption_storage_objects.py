"""In-memory storage contract vs encryption (Slice 8.11).

The in-memory store does **not** cryptographically encrypt bytes. These tests
cover product-contract behavior only: digests/identity are independent of
encryption mode, receipts omit key identifiers, and accepted/quarantine paths
share the same encryption policy posture.
"""

from __future__ import annotations

import json

from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
    default_encryption_policy,
)
from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    build_quarantine_storage_object,
)

from ._envelope_test_helpers import make_envelope
from ._quarantine_test_helpers import make_quarantine_record

LAKE_POLICY = CommunityDataLakePolicy.default()


def test_in_memory_store_does_not_claim_cryptographic_encryption() -> None:
    """Contract note: in-memory models write semantics; it does not encrypt."""

    policy = default_encryption_policy()
    assert "in_memory_store_does_not_cryptographically_encrypt" in policy.limitations
    store = InMemoryCommunityDataLakeStore()
    result = store.put_immutable_event(make_envelope())
    assert result.status is StorageWriteStatus.STORED
    assert result.receipt is not None
    # Stored payload remains canonical plaintext JSON bytes in-process.
    assert result.receipt.content_sha256.startswith("sha256:")
    public = result.receipt.to_public_dict()
    assert "encryption" not in public
    assert "kms" not in json.dumps(public).lower()
    assert "ServerSideEncryption" not in public


def test_content_digest_independent_of_encryption_policy() -> None:
    envelope = make_envelope()
    obj = build_immutable_raw_storage_object(envelope, LAKE_POLICY)
    # Encryption mode is not part of object identity / digest computation.
    assert "sse_s3" not in obj.object_key
    assert "aes256" not in obj.object_key.lower()
    assert "encryption" not in obj.to_s3_metadata()
    assert "kms" not in json.dumps(obj.to_s3_metadata()).lower()


def test_quarantine_receipt_omits_encryption_key_identifiers() -> None:
    store = InMemoryCommunityDataLakeStore()
    result = store.quarantine_event(make_quarantine_record())
    assert result.status is StorageWriteStatus.STORED
    assert result.quarantine_receipt is not None
    public = result.quarantine_receipt.to_public_dict()
    blob = json.dumps(public, sort_keys=True).lower()
    for token in ("kms_key", "key_arn", "key_id", "server_side_encryption", "aes256"):
        assert token not in blob


def test_accepted_and_quarantine_share_encryption_policy_parity() -> None:
    policy = default_encryption_policy()
    assert policy.accepted_prefix_encrypted is True
    assert policy.quarantine_prefix_encrypted is True
    assert policy.encryption_mode == "sse_s3"
    accepted = build_immutable_raw_storage_object(make_envelope(), LAKE_POLICY)
    quarantine = build_quarantine_storage_object(make_quarantine_record())
    assert accepted.object_key.startswith("raw/")
    assert quarantine.object_key.startswith("quarantine/")
    # Neither path embeds encryption mode into object identity.
    assert accepted.content_sha256.startswith("sha256:")
    assert quarantine.content_sha256.startswith("sha256:")
