from infrastructure.verification.packaging import check_packaging


def test_packaging() -> None:
    results = check_packaging()
    assert results and all(item.ok for item in results)
