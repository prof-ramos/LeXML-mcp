# LeXML-mcp

**MCP server for LexML Brasil** — search the legislative SRU acervo, resolve URNs, and inspect service metadata. Built with FastMCP + httpx.

## Features

| Tool | Description |
|------|-------------|
| `lexml_search` | Search the LexML SRU acervo with CQL queries |
| `lexml_resolve_urn` | Resolve a LexML URN to its public URL |
| `lexml_explain` | Retrieve metadata about the SRU service |

Every response includes a **provenance envelope** (`source_url`, `source_kind`, `authority`, `retrieved_at`, `content_hash`, `backend_name`, `backend_version`, `schema_version`).

## Quick start

```bash
# Install
uv sync

# Run the server (stdio transport)
uv run lexml-mcp
```

The server listens on **stdio** — configure your MCP client to launch it:

```json
{
  "mcpServers": {
    "lexml": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/LeXML-mcp", "lexml-mcp"]
    }
  }
}
```

## Usage examples

### lexml_search

```python
# Search for documents about consumer protection law
result = await lexml_search(
    query='dc.title any "código de defesa do consumidor"',
    start_record=1,
    maximum_records=10,
    record_schema="dc"
)
```

Returns structured records with Dublin Core fields, `number_of_records`, `next_record_position`, and provenance.

### lexml_resolve_urn

```python
# Resolve a URN to its public URL
result = await lexml_resolve_urn(
    urn="urn:lex:br:federal:lei:1990-09-11;8078"
)
```

Returns `public_url`, `status_code`, `redirect_chain`, and provenance.

### lexml_explain

```python
# Inspect SRU service capabilities
result = await lexml_explain()
```

Returns SRU explain record data with server info, database info, and supported schemas.

## Challenge detection

The SRU endpoint may return an HTML verification page instead of XML. The server detects this and returns a structured object:

```json
{
  "is_challenge_like": true,
  "content_type": "text/html",
  "raw_excerpt": "<!DOCTYPE html>...",
  "status_code": 200,
  "provenance": { ... }
}
```

## Error handling

All errors are returned as structured objects — never crashes:

| Error type | Trigger |
|------------|---------|
| `network_error` | Connection refused, DNS failure |
| `timeout` | Request exceeded timeout (default 15s) |
| `invalid_xml` | SRU returned malformed XML |
| `http_error` | Non-2xx HTTP status |

## Caching

LRU cache with configurable TTL (default 300s, max 256 entries). Challenges are never cached as successes. Configure via environment:

- `LEXML_CACHE_TTL` — seconds (default `300`)
- `LEXML_CACHE_MAXSIZE` — max entries (default `256`)

## Configuration

| Env variable | Default | Description |
|-------------|---------|-------------|
| `LEXML_SRU_URL` | `https://www.lexml.gov.br/busca/SRU` | SRU endpoint |
| `LEXML_URN_TEMPLATE` | `https://www.lexml.gov.br/urn/{urn}` | URN resolution template |
| `LEXML_TIMEOUT` | `15.0` | HTTP request timeout (seconds) |
| `LEXML_CACHE_TTL` | `300` | Cache TTL (seconds) |
| `LEXML_CACHE_MAXSIZE` | `256` | Max cache entries |

## Project structure

```
src/lexml_mcp/
├── server.py              # FastMCP server, tool registration
├── config.py              # Environment-based configuration
├── connectors/
│   └── acervo.py          # SRU search, explain, URN resolution
├── models/
│   ├── provenance.py      # Provenance envelope
│   ├── search.py          # Search result models
│   └── error.py           # Structured error objects
└── utils/
    ├── cache.py           # LRU TTL cache
    └── challenge.py       # Challenge HTML detection
```

## Testing

```bash
uv run pytest
```

29 tests covering:
- SRU success parsing (Dublin Core records)
- Challenge HTML detection
- Malformed XML handling
- Timeout simulation
- URN resolution
- Explain response parsing
- Provenance envelope construction
- Cache set/get/expiry/eviction
- Structured error types
- Tool registration

## Limitations

- **Parser, linker, renderer not implemented** — these require JVM/Scala/Haskell infrastructure and are roadmap items
- **SRU endpoint may return challenge HTML** — the server detects and reports this transparently
- **No multi-tenancy** — single-user, local-first design
- **No DOCX output** — renderer integration is future scope
- **No Unicode normalization** — preserves original content as-is
- **No external health checks** — liveness is local only

## Dependencies

- `mcp` — official Python SDK (FastMCP)
- `httpx` — async HTTP client
- stdlib only beyond those two

## License

GPL-3.0-or-later