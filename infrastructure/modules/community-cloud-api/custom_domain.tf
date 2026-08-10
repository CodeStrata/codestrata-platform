# Slice 17.14 — Regional custom domain api.codestrata.ai for the existing HTTP API.
#
# ACM certificate (us-west-2) + API Gateway HTTP API custom domain + stage mapping.
# Default execute-api endpoint remains enabled (FALLBACK_IMPLEMENTATION_ENDPOINT).
# Cloudflare DNS (DNS-only, not proxied) is configured via
# infrastructure/scripts/configure-api-domain-dns.sh after ACM validation records
# are known — zone remains Cloudflare-managed outside OpenTofu.

resource "aws_acm_certificate" "api_custom_domain" {
  count = var.enable_api_custom_domain ? 1 : 0

  domain_name       = var.api_custom_domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Component = "community-cloud-api-domain"
    Slice     = "17.14"
  })
}

resource "aws_apigatewayv2_domain_name" "api" {
  count = var.enable_api_custom_domain ? 1 : 0

  domain_name = var.api_custom_domain_name

  domain_name_configuration {
    certificate_arn = aws_acm_certificate_validation.api_custom_domain[0].certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  tags = merge(local.common_tags, {
    Component = "community-cloud-api-domain"
    Slice     = "17.14"
  })
}

resource "aws_apigatewayv2_api_mapping" "api" {
  count = var.enable_api_custom_domain ? 1 : 0

  api_id      = aws_apigatewayv2_api.community_cloud.id
  domain_name = aws_apigatewayv2_domain_name.api[0].id
  stage       = aws_apigatewayv2_stage.production.name
  # Empty mapping key preserves /api/v1/... paths (no prefix duplication).
}

# Validation waits until Cloudflare (or other DNS) publishes ACM CNAMEs.
# configure-api-domain-dns.sh upserts those records from tofu outputs.
resource "aws_acm_certificate_validation" "api_custom_domain" {
  count = var.enable_api_custom_domain ? 1 : 0

  certificate_arn         = aws_acm_certificate.api_custom_domain[0].arn
  validation_record_fqdns = [for dvo in aws_acm_certificate.api_custom_domain[0].domain_validation_options : dvo.resource_record_name]

  timeouts {
    create = "45m"
  }
}
