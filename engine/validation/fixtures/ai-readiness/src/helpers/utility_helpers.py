"""Generic helper — must NOT become MCP/tool or agent evidence.

Static validation only. Do not execute. Not under tools/ or mcp/.
"""


def format_label(value: str) -> str:
    """Ordinary utility function (not an MCP tool definition)."""
    return value.strip().lower()
