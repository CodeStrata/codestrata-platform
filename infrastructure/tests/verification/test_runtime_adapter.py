from infrastructure.verification.runtime_adapter import check_runtime_adapter


def test_runtime_adapter() -> None:
    results = check_runtime_adapter()
    assert results and all(item.ok for item in results), [r for r in results if not r.ok]
