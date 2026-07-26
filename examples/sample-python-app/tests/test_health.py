from sample_python_app.app import health


def test_health() -> None:
    assert health()["status"] == "ok"
