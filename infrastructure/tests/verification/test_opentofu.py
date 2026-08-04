from infrastructure.verification.opentofu import check_opentofu_contract, detect_tools


def test_opentofu_contract() -> None:
    tools = detect_tools()
    results = check_opentofu_contract(tools)
    assert results and all(item.ok for item in results)
    assert tools.opentofu_validation_status in {
        "pass",
        "fail",
        "not_executed_tool_unavailable",
        "pending",
    }
