from infrastructure.verification.configuration import check_configuration


def test_configuration() -> None:
    results = check_configuration()
    assert results and all(item.ok for item in results)
