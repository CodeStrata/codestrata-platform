"""Stream-agnostic object-key-vs-policy partition validation (Slice 8.4).

Every helper here is deliberately stream-agnostic: it only needs an object
key, a :class:`~.partition_policies.StreamPartitionPolicy`, and (for the
cross-check helper) the :class:`~.envelopes.DataLakeEnvelope` the key was
built from. No stream-specific field (``assessment_schema_version``,
``language``, ``heads``, ...) is ever inspected here — those live in each
stream's own partitioning module (see
:mod:`.streams.assessment_metadata_partitioning`).
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.partition_policies import (
    StreamPartitionPolicy,
)
from codestrata_platform.community_cloud_api.data_lake.partitions import (
    ACCEPTED_ROOT,
    PartitionKeyError,
    assert_key_excludes_identity_material,
)
from codestrata_platform.community_cloud_api.data_lake.validation import (
    DataLakeValidationError,
    validate_partition_date,
)


class StreamPartitionError(ValueError):
    """Raised when an object key does not structurally match its stream's partition policy.

    Distinct from :class:`~.partition_policies.PartitionPolicyError` (a
    malformed *policy*) and :class:`~.partitions.PartitionKeyError` (a
    malformed *key*, independent of any policy) — this is specifically a
    key-vs-policy (or key-vs-envelope) mismatch.
    """


def parse_hive_dimensions(object_key: str) -> dict[str, str]:
    """Parse the ``key=value`` Hive segments between the root prefix and filename.

    Returns an insertion-ordered mapping of dimension name to raw string
    value. Raises :class:`StreamPartitionError` for any non-``key=value``
    segment, any blank key/value, a duplicated dimension name, or a key with
    fewer than three ``/``-separated segments (root, at least one dimension,
    filename).
    """

    segments = object_key.split("/")
    if len(segments) < 3:
        raise StreamPartitionError("object_key has too few path segments to carry partitions")

    hive_segments = segments[1:-1]
    dimensions: dict[str, str] = {}
    for segment in hive_segments:
        if "=" not in segment:
            raise StreamPartitionError(f"malformed partition segment: {segment!r}")
        name, _, value = segment.partition("=")
        if not name or not value:
            raise StreamPartitionError(f"malformed partition segment: {segment!r}")
        if name in dimensions:
            raise StreamPartitionError(f"duplicate partition dimension: {name!r}")
        dimensions[name] = value
    return dimensions


def assert_partition_bounds(object_key: str, policy: StreamPartitionPolicy) -> None:
    """Fail-closed key-length and dimension-depth checks against ``policy`` alone."""

    if len(object_key) > policy.max_key_length:
        raise StreamPartitionError(
            f"object_key length {len(object_key)} exceeds policy max_key_length "
            f"{policy.max_key_length}"
        )
    dimensions = parse_hive_dimensions(object_key)
    if len(dimensions) > policy.max_partition_depth:
        raise StreamPartitionError(
            f"object_key has {len(dimensions)} partition dimensions, exceeding policy "
            f"max_partition_depth {policy.max_partition_depth}"
        )


def assert_partition_dimensions_allowed(
    object_key: str, policy: StreamPartitionPolicy
) -> dict[str, str]:
    """Fail-closed dimension-name checks: required present, no unlisted/forbidden extras.

    Returns the parsed dimension mapping on success.
    """

    dimensions = parse_hive_dimensions(object_key)
    allowed = set(policy.required_path_dimensions) | set(policy.optional_path_dimensions)
    for name in dimensions:
        if name not in allowed:
            raise StreamPartitionError(
                f"unlisted partition dimension not permitted by policy: {name!r}"
            )
    for name in policy.forbidden_partition_fields:
        if name in dimensions:
            raise StreamPartitionError(f"forbidden partition dimension present: {name!r}")
    for name in policy.required_path_dimensions:
        if name not in dimensions:
            raise StreamPartitionError(f"missing required partition dimension: {name!r}")
    return dimensions


def assert_partition_key_matches_policy(
    object_key: str,
    policy: StreamPartitionPolicy,
    envelope: DataLakeEnvelope,
) -> dict[str, str]:
    """Fail-closed structural check of ``object_key`` against ``policy`` and ``envelope``.

    Verifies, in order:

    1. ``object_key`` excludes raw identity material (delegates to
       :func:`~.partitions.assert_key_excludes_identity_material`).
    2. ``object_key`` lives under the accepted root prefix (``raw/``) — this
       helper never validates quarantine keys.
    3. Key length and partition-dimension-count bounds from ``policy``.
    4. Every ``required_path_dimensions`` entry is present and no unlisted or
       ``forbidden_partition_fields`` dimension is present — this is what
       rejects any silently-added extra Hive dimension (``client_type=``,
       ``language=``, etc.) beyond the policy's declared generic set.
    5. The ``stream=`` and ``schema_version=`` dimension values match
       ``envelope.event_stream`` / ``envelope.source_schema_version``.
    6. The ``year=``/``month=``/``day=`` dimension values are well-formed
       partition-date components matching ``envelope.accepted_year`` /
       ``accepted_month`` / ``accepted_day``.

    Returns the parsed dimension mapping on success. Raises
    :class:`StreamPartitionError` on any mismatch — never leaks the raw
    payload, only dimension names/values already present in the key.
    """

    try:
        assert_key_excludes_identity_material(object_key)
    except PartitionKeyError as exc:
        raise StreamPartitionError(str(exc)) from exc

    if not object_key.startswith(f"{ACCEPTED_ROOT}/"):
        raise StreamPartitionError("object_key must live under the accepted root prefix")

    assert_partition_bounds(object_key, policy)
    dimensions = assert_partition_dimensions_allowed(object_key, policy)

    if dimensions.get("stream") != envelope.event_stream:
        raise StreamPartitionError("partition 'stream' dimension does not match envelope")
    if dimensions.get("schema_version") != envelope.source_schema_version:
        raise StreamPartitionError(
            "partition 'schema_version' dimension does not match envelope"
        )

    try:
        year, month, day = validate_partition_date(
            dimensions.get("year", ""), dimensions.get("month", ""), dimensions.get("day", "")
        )
    except DataLakeValidationError as exc:
        raise StreamPartitionError(str(exc)) from exc

    if (year, month, day) != (
        envelope.accepted_year,
        envelope.accepted_month,
        envelope.accepted_day,
    ):
        raise StreamPartitionError(
            "partition year/month/day dimensions do not match envelope acceptance date"
        )

    return dimensions


def assert_s3_metadata_matches_policy(
    metadata: dict[str, str], policy: StreamPartitionPolicy
) -> None:
    """Fail-closed check that every ``metadata`` key is in ``policy.s3_metadata_allowlist``."""

    offending = set(metadata) - policy.s3_metadata_allowlist
    if offending:
        raise StreamPartitionError(
            f"S3 metadata keys not allowlisted by policy: {sorted(offending)}"
        )
