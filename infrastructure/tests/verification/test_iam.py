from infrastructure.verification.iam import check_iam


def test_iam() -> None:
    results = check_iam()
    assert results and all(item.ok for item in results)
