from infrastructure.verification.structure import check_structure


def test_structure() -> None:
    results = check_structure()
    assert results and all(item.ok for item in results)
