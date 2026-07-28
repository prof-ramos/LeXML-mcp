# LexML MCP — Contract Documentation

## Response Envelope

Every tool returns a `ResponseEnvelope` with the following shape:

```json
{
  "success": bool,
  "partial_success": bool,
  "schema_version": "1.0",
  "operation": "lexml_search | lexml_resolve_urn | lexml_explain",
  "data": { ... } | null,
  "errors": [
    {
      "code": "ERROR_CODE",
      "message": "Human-readable description",
      "retryable": bool,
      "details": { ... } | null,
      "record_position": int | null
    }
  ],
  "warnings": [],
  "provenance": {
    "source_urn": str | null,
    "source_url": str | null,
    "source_kind": "sru | urn",
    "authority": "lexml.gov.br",
    "retrieved_at": "ISO8601 timestamp",
    "content_hash": "sha256 prefix (16 chars)",
    "backend_name": "lexml-mcp",
    "backend_version": "0.2.0",
    "schema_version": "1.0"
  },
  "diagnostics": [
    { "uri": "info:srw/diagnostic/...", "message": "..." }
  ],
  "cache_status": "hit | miss | bypassed"
}
```

## Input Contracts

### lexml_search

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| query | str | None | CQL query string. Mutually exclusive with filters. |
| start_record | int | 1 | First record position |
| maximum_records | int | 10 | Max records (capped at 100) |
| record_schema | str | "dc" | Schema (allowed: dc, oai_dc) |
| filters | dict | None | Structured filters. Mutually exclusive with query. |

**filters dict:**
```json
{
  "title": "string",
  "terms": ["string", "..."],
  "document_type": "string",
  "authority": "string",
  "date_from": "YYYY-MM-DD",
  "date_to": "YYYY-MM-DD"
}
```

### lexml_resolve_urn

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| urn | str | required | LexML URN (e.g. urn:lex:br:federal:lei:1990-09-11;8078) |
| verify | bool | false | Follow redirects and validate final host |

### lexml_explain

No parameters.

## Output Contracts

### lexml_search — data shape

```json
{
  "request_url": "string",
  "content_type": "string",
  "number_of_records": int,
  "next_record_position": int | null,
  "records": [
    {
      "record_position": int,
      "record_schema": "dc | oai_dc",
      "data": { "field": "value" | ["value1", "value2"] },
      "field_values": { "field": ["value1", "value2", ...] }
    }
  ],
  "diagnostics": [ ... ]
}
```

### lexml_resolve_urn — data shape (verify=false)

```json
{
  "urn": "string",
  "public_url": "string"
}
```

### lexml_resolve_urn — data shape (verify=true)

```json
{
  "urn": "string",
  "public_url": "string",
  "status_code": int,
  "redirect_chain": [
    { "url": "string", "status": int }
  ]
}
```

### lexml_explain — data shape

Same as search but with explain record data.

## Error Response

On error, `success` is `false`, `data` is `null`, and `errors` array contains the error details.