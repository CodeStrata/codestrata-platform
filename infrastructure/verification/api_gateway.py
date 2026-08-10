"""API Gateway static verification."""

from __future__ import annotations

from infrastructure.verification.contract import infra_root
from infrastructure.verification.models import CheckResult


def check_api_gateway() -> list[CheckResult]:
    text = (
        infra_root() / "modules" / "community-cloud-api" / "api_gateway.tf"
    ).read_text(encoding="utf-8")
    module = "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted((infra_root() / "modules" / "community-cloud-api").glob("*.tf"))
    )
    return [
        CheckResult(
            name="apigw:http_api",
            ok='resource "aws_apigatewayv2_api"' in text
            and 'protocol_type = "HTTP"' in text,
            detail="HTTP API",
            category="api_gateway",
            scenario="G",
        ),
        CheckResult(
            name="apigw:no_rest_api",
            ok='resource "aws_api_gateway_rest_api"' not in module,
            detail="no REST API",
            category="api_gateway",
            scenario="G",
        ),
        CheckResult(
            name="apigw:lambda_proxy",
            ok='integration_type       = "AWS_PROXY"' in text
            or 'integration_type = "AWS_PROXY"' in text,
            detail="AWS_PROXY",
            category="api_gateway",
            scenario="H",
        ),
        CheckResult(
            name="apigw:payload_2_0",
            ok='payload_format_version = "2.0"' in text,
            detail="2.0",
            category="api_gateway",
        ),
        CheckResult(
            name="apigw:catch_all_proxy",
            ok='route_key = "ANY /{proxy+}"' in text and 'route_key = "ANY /"' in text,
            detail="proxy routes",
            category="api_gateway",
        ),
        CheckResult(
            name="apigw:stage_throttling",
            ok="throttling_burst_limit" in text and "throttling_rate_limit" in text,
            detail="stage throttling",
            category="api_gateway",
        ),
        CheckResult(
            name="apigw:no_authorizer",
            ok="aws_apigatewayv2_authorizer" not in module
            and "cognito" not in module.lower(),
            detail="no authorizer/cognito",
            category="api_gateway",
        ),
        CheckResult(
            name="apigw:custom_domain_present",
            ok="aws_apigatewayv2_domain_name" in module
            and "aws_acm_certificate" in module
            and "api.codestrata.ai" in module,
            detail="api.codestrata.ai ACM+domain",
            category="api_gateway",
            scenario="G",
        ),
        CheckResult(
            name="apigw:no_waf_cors",
            ok="aws_wafv2" not in module and "cors_configuration" not in text,
            detail="no waf/cors",
            category="api_gateway",
        ),
        CheckResult(
            name="apigw:execute_api_retained",
            ok="execute_api_endpoint_retained" in module or "FALLBACK" in module
            or 'disable_execute_api_endpoint' not in module,
            detail="execute-api fallback retained",
            category="api_gateway",
        ),
        CheckResult(
            name="apigw:one_api",
            ok=module.count('resource "aws_apigatewayv2_api"') == 1,
            detail="one HTTP API",
            category="api_gateway",
        ),
    ]
