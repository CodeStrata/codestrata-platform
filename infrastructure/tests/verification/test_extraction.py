from infrastructure.verification.extraction import check_extraction


def test_extraction() -> None:
    results = check_extraction()
    assert results and all(item.ok for item in results)
