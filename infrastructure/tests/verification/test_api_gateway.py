from infrastructure.verification.api_gateway import check_api_gateway


def test_api_gateway() -> None:
    results = check_api_gateway()
    assert results and all(item.ok for item in results)
