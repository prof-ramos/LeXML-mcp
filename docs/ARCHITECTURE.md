# Architecture

## Layers

```
src/lexml_mcp/
├── server.py          # FastMCP server — tool registration, CQL builder, entry point
├── config.py          # Environment-based configuration (SRU_URL, timeouts, cache)
├── connectors/
│   └── acervo.py      # HTTP client — SRU search, explain, URN resolution
├── models/
│   ├── envelope.py    # ResponseEnvelope + make_envelope() — every tool returns this shape
│   ├── provenance.py  # Provenance dataclass — source tracking per response
│   ├── error.py       # StructuredError + ErrorCode — never crash, always return structured errors
│   └── search.py      # SearchRecord / SearchResult dataclasses
└── utils/
    ├── cache.py       # TTLCache — LRU + TTL, thread-safe (OrderedDict + Lock)
    └── challenge.py   # is_challenge_html — detect HTML verification pages
```

### Server layer

`server.py` owns three tools and one resource. Each tool:
1. Validates input (mutual exclusivity of `query` vs `filters`)
2. Checks the LRU cache (keyed by operation+params)
3. Delegates to the connector layer
4. Wraps the result in a `ResponseEnvelope` via `make_envelope()`

### Connector layer

`acervo.py` is the sole HTTP client. Every external call goes through `_fetch_and_parse()` which:
1. Builds a `Provenance` envelope
2. Issues an `httpx.AsyncClient.get()` with configurable timeout and redirect limits
3. Detects challenge HTML before parsing XML
4. Parses XML with `defusedxml` (entity-expansion safe)
5. Returns a plain dict (never raises)

### Models layer

- `ResponseEnvelope` — standard shape: `{success, data, errors, warnings, provenance, diagnostics}`
- `Provenance` — source attribution: `{source_url, source_kind, authority, retrieved_at, content_hash, backend_name, backend_version, schema_version}`
- `StructuredError` / `ErrorCode` — typed error containers with retryable flag

### Utils layer

- `TTLCache` — in-memory LRU with per-key TTL expiry, thread-safe via `Lock`
- `challenge.py` — heuristic detection of challenge/verification HTML pages

## Tool flow

```
Client → FastMCP → tool function
                       ├─ validate input
                       ├─ cache lookup (LRU)
                       ├─ acervo.sru_search/sru_explain/resolve_urn
                       │    ├─ Provenance.build()
                       │    ├─ httpx GET
                       │    ├─ is_challenge_html? → return challenge object
                       │    ├─ defusedxml parse
                       │    └─ _parse_sru_response()
                       ├─ cache set (on success)
                       └─ make_envelope() → ResponseEnvelope
```

## Architectural decisions

- **All-HTTP-over-stdio** — no SSE, no WebSocket. Single stdio transport. The MCP client manages the process lifecycle.
- **Plain dicts, not exceptions** — every path returns a dict. Tools never raise. Error codes are data, not control flow.
- **Connector as sole I/O boundary** — `acervo.py` is the only module with network calls. `server.py` and models are pure logic.
- **Provenance on every response** — every tool output includes who, what, when, and where the data came from.
- **No async framework lock-in** — FastMCP is the only async dependency. The connector uses bare `httpx.AsyncClient`, not framework-specific clients.
- **Memory-only cache** — LRU in process. No persistence. A SQLite-backed cache is a TODO item once persistence requirements emerge.
