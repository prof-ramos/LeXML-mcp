# Changelog

## 0.1.0 — 2026-07-27

Initial release of LeXML-mcp, a FastMCP server for LexML Brasil.

### Features

- **lexml_search** — Search the LexML SRU acervo with CQL queries or structured filters (title, subjects, authority, date range). Returns Dublin Core records with pagination.
- **lexml_resolve_urn** — Resolve a LexML URN (e.g. `urn:lex:br:federal:lei:1990-09-11;8078`) to its public URL. Follows redirects, validates final host.
- **lexml_explain** — Retrieve SRU explain metadata: server info, database info, supported schemas.
- **lexml://sru/explain resource** — Static resource exposing cached explain data.

### Architecture

- **ResponseEnvelope** — Standardized response shape: `{success, data, errors, warnings, provenance, diagnostics}` on every tool call.
- **Provenance** — Per-response source tracking: `source_url`, `source_kind`, `authority`, `retrieved_at`, `content_hash`, `backend_name`, `backend_version`, `schema_version`.
- **Structured error codes** — `INVALID_INPUT`, `INVALID_CQL`, `INVALID_URN`, `UPSTREAM_CHALLENGE`, `UPSTREAM_TIMEOUT`, `UPSTREAM_HTTP_ERROR`, `INVALID_XML`, `SRU_DIAGNOSTIC`, `INTERNAL_ERROR`. Retryable flag for transient failures.
- **CQL filter builder** — Structured filter → safe CQL generation. User values escaped (quote doubling). No string concatenation of raw input.
- **LRU TTL cache** — In-process memory cache (configurable TTL and max size). Challenges never cached.

### Security

- **defusedxml** — All XML parsing uses defusedxml, blocking entity expansion and XXE.
- **URN validation** — Regex-based syntax check; host allowlist on resolved URLs (SSRF guard).
- **Challenge detection** — Content-type and body heuristics detect HTML verification pages before XML parsing.

### Testing

61 tests covering: SRU success parsing, challenge detection (HTML, 403, 429, 500), malformed XML, DTD entity expansion, timeout simulation, URN resolution (success, timeout, ssrf block), explain response, structured error codes, provenance envelope, cache (set/get/expiry/eviction/invalidate/clear), envelope wrapping, CQL filter generation, resource registration, tool registration.
