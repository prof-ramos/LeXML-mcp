# TODO

Items deferred from the initial release. All depend on external validation, user demand, or technical spike before implementation.

## Priority

### Parser (lexml-parser bridge)

- Integrate with [lexml-parser](https://github.com/lexml/lexml-parser) (JVM) or [lexml-scala](https://github.com/lexml/lexml-scala) for structured document parsing.
- Requires: spike on JVM interop (subprocess, REST proxy, or GraalVM native image).
- Blocked on: user validation that parser output is needed in MCP context.

### Linker (normative reference resolution)

- Resolve normative references within parsed documents (links between laws, decrees, amendments).
- Requires: parser output first. The linker operates on parsed document ASTs.

### Renderer (DOCX / HTML)

- Render parsed+linked documents as .docx, .html, or plain text.
- Requires: parser and linker outputs. Template engine selection depends on output format requirements.

### SQLite cache

- Replace in-memory LRU with persistent SQLite cache for cross-process caching and server restarts.
- Requires: measurable benefit over LRU — not justified until multi-tenancy or long-running deployments.

### Streamable HTTP transport

- Add SSE-based Streamable HTTP transport in addition to stdio.
- Requires: MCP SDK support for dual transport, or spike on manual implementation.
- Blocked on: user demand for HTTP-based client integration.

### Observability

- Structured logging (structlog / loguru).
- Prometheus metrics (request count, latency, cache hit ratio).
- Health check endpoint.
- Blocked on: deployment environment and monitoring requirements.
