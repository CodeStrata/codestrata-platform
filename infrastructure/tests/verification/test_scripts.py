from infrastructure.verification.scripts import check_scripts


def test_scripts() -> None:
    results = check_scripts()
    assert results and all(item.ok for item in results)
