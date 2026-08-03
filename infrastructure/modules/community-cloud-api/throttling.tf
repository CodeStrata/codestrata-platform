# API Gateway stage throttling is defined on aws_apigatewayv2_stage in
# api_gateway.tf (default_route_settings).
#
# This file documents the dual-layer rate-limit posture for Slice 7.14:
#
# 1. API Gateway stage throttling — deployment-level outer protection
# 2. Application process-local InMemoryRateLimitStore — defense-in-depth only
#
# Neither provides durable per-client distributed quotas equivalent to a
# shared store. Authenticated distributed client quotas are not implemented.
# Ingestion remains fail-closed due to unavailable authentication verifier
# and sinks regardless of throttling.

locals {
  throttling_documentation = {
    api_gateway_burst = var.api_throttle_burst_limit
    api_gateway_rate  = var.api_throttle_rate_limit
    application_mode  = var.rate_limit_mode
    distributed       = false
  }
}
