# CodeStrata Community Data Lake — Slice 8.1 foundation.
#
# This module creates a single private, encrypted, versioned S3 bucket with
# prefix-based isolation (raw/ accepted, quarantine/ rejected-or-pending).
# It does not attach the bucket to any compute, queue, or event source.
# Bucket existence does not enable ingestion — see enable_ingestion_wire in
# variables.tf and validation.tf, and README.md for the fail-closed posture.
#
# Shared naming/tagging locals live in locals.tf. Resources are split across
# storage.tf, encryption.tf, lifecycle.tf, iam.tf, and bucket_policy.tf.
