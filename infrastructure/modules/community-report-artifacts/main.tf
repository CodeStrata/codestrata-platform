# CodeStrata Community Report Artifact Store — Slice 17.16.
#
# Private S3 boundary for Assessment / Engineering Intelligence report files.
# Separate from Community Data Lake (telemetry/events only).
# No website hosting, no public ACL/policy, no Athena/Glue/DynamoDB/RDS.
# Product-visible retention is application-enforced (current+previous only).
# S3 Versioning is operational recovery only — not product report history.
