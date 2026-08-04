from infrastructure.verification.safety import check_safety


def test_safety() -> None:
    results = check_safety()
    assert results and all(item.ok for item in results)
