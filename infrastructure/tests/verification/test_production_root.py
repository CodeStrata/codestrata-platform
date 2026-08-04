from infrastructure.verification.production_root import check_production_root


def test_production_root() -> None:
    results = check_production_root()
    assert results and all(item.ok for item in results)
