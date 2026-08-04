from infrastructure.verification.lambda_config import check_lambda_config


def test_lambda_config() -> None:
    results = check_lambda_config()
    assert results and all(item.ok for item in results)
