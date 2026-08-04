from infrastructure.verification.logging_checks import check_logging


def test_logging() -> None:
    results = check_logging()
    assert results and all(item.ok for item in results)
