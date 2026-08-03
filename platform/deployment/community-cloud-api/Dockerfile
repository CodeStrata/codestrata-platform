# Community Cloud API — AWS Lambda container image (Platform-owned packaging).
# Build context: repository root (see infrastructure/scripts/build-community-cloud-api.sh).
# Do not include tests, docs, demos, governance, or secrets.

ARG PYTHON_VERSION=3.12
FROM public.ecr.aws/lambda/python:${PYTHON_VERSION}

# Install Engine + Platform runtime only (no docs/tests).
COPY engine/pyproject.toml /tmp/engine/pyproject.toml
COPY engine/README.md /tmp/engine/README.md
COPY engine/LICENSE /tmp/engine/LICENSE
COPY engine/MANIFEST.in /tmp/engine/MANIFEST.in
COPY engine/src /tmp/engine/src
COPY platform/pyproject.toml /tmp/platform/pyproject.toml
COPY platform/README.md /tmp/platform/README.md
COPY platform/src /tmp/platform/src

RUN pip install --no-cache-dir "/tmp/engine" "/tmp/platform[lambda]" \
    && rm -rf /tmp/engine /tmp/platform /root/.cache/pip

# Fail-closed production foundation defaults (overridable by Lambda env).
ENV CODESTRATA_DEPLOYMENT_MODE=production_foundation \
    CODESTRATA_COMMUNITY_API_VERSION=1.0 \
    CODESTRATA_AUTHENTICATION_ENABLED=true \
    CODESTRATA_RATE_LIMIT_ENABLED=true \
    CODESTRATA_INGESTION_ENABLED=false \
    CODESTRATA_AUTHENTICATION_MODE=enabled_verifier_unavailable \
    CODESTRATA_RATE_LIMIT_MODE=api_gateway_plus_process_local \
    PYTHONUNBUFFERED=1

# Lambda base image runs as a non-root user for the runtime process.
CMD ["codestrata_platform.community_cloud_api.deployment.lambda_handler.handler"]
