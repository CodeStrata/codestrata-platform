from infrastructure.verification.ecr import check_ecr


def test_ecr() -> None:
    results = check_ecr()
    assert results and all(item.ok for item in results)
