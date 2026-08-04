from infrastructure.verification.state import check_state


def test_state() -> None:
    results = check_state()
    assert results and all(item.ok for item in results)
