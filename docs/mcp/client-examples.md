# MCP Client Examples

Placeholders only — do not embed secrets, usernames, or absolute private paths.

## Cursor

```json
{
  "mcpServers": {
    "codestrata": {
      "command": "/path/to/.venv/bin/aimf",
      "args": ["mcp", "serve", "--config", "/path/to/aimf.toml"]
    }
  }
}
```

Enable `[mcp].enabled = true` and the knowledge retrieval/answering gates you need.

## Claude Desktop

```json
{
  "mcpServers": {
    "codestrata": {
      "command": "/path/to/.venv/bin/aimf",
      "args": ["mcp", "serve", "--config", "/path/to/aimf.toml"]
    }
  }
}
```

## Generic streamable HTTP (localhost)

```bash
aimf mcp serve --config aimf.toml --transport http --host 127.0.0.1 --port 8765
```

Point an MCP HTTP client at `http://127.0.0.1:8765/mcp` (SDK default path).
Do not expose this port publicly.

## Example tool calls

```json
{
  "name": "repository_search",
  "arguments": {
    "query": "How is authentication implemented?",
    "tenant_id": "example-tenant",
    "repository_id": "example-repo",
    "top_k": 5
  }
}
```

```json
{
  "name": "repository_answer",
  "arguments": {
    "question": "What are the highest-severity security findings?",
    "tenant_id": "example-tenant",
    "repository_id": "example-repo",
    "answer_style": "findings_summary"
  }
}
```

`repository_answer` returns deterministic extractive statements with `SRC-*`
citations — not production generative AI.
