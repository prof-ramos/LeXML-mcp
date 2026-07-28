# LexML MCP — Roadmap

## Near-term (v0.3)

- [ ] **SRU explain metadata**: expose database info, indexes, schemas from explain response
- [ ] **Record schema negotiation**: support oai_dc and other schemas
- [ ] **Pagination helper**: convenience method for iterating through multi-page results
- [ ] **Configurable record limit**: per-request cap via LEXML_MAXIMUM_RECORDS_LIMIT

## Medium-term (v0.4–v0.5)

- [ ] **Result caching**: SQLite-backed persistent cache (optional)
- [ ] **Metrics**: request counters, latency histograms, error rate (Prometheus)
- [ ] **Streamable HTTP**: MCP Streamable HTTP transport support
- [ ] **Authentication**: optional API key / bearer token for production deployments

## Long-term (v1.0+)

- [ ] **DOCX export**: render search results as .docx
- [ ] **Multi-tenancy**: isolated caches and rate limits per tenant
- [ ] **Redis cache backend**: distributed cache for multi-instance deployments
- [ ] **Parser**: structured field extraction from raw SRU records
- [ ] **Linker**: cross-reference resolution between related legal documents
- [ ] **Renderer**: HTML/PDF rendering of legal documents

## Non-goals

- Full-text search index (delegated to LexML SRU)
- User management
- Web UI