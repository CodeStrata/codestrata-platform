from infrastructure.verification.module_contract import check_module_contract


def test_module_contract() -> None:
    results = check_module_contract()
    assert results and all(item.ok for item in results)
