# LexML MCP — Error Catalog

## Error Codes

| Code | Retryable | Description |
|------|-----------|-------------|
| INVALID_INPUT | No | Invalid input provided |
| INVALID_CQL | No | Invalid CQL query syntax |
| INVALID_URN | No | Invalid URN syntax or disallowed host |
| UPSTREAM_CHALLENGE | Yes | Upstream returned a challenge/verification page |
| UPSTREAM_TIMEOUT | Yes | Upstream request timed out |
| UPSTREAM_HTTP_ERROR | Yes | Upstream returned an HTTP error |
| INVALID_XML | No | Invalid XML from upstream |
| SRU_DIAGNOSTIC | No | SRU diagnostic returned |
| INTERNAL_ERROR | No | Internal server error |
| INVALID_RECORD_SCHEMA | No | Invalid record schema |
| PAYLOAD_TOO_LARGE | No | Request payload too large |
| RESPONSE_TOO_LARGE | No | Upstream response exceeded size limit |
| UPSTREAM_RATE_LIMITED | Yes | Upstream rate limited the request |
| UNSAFE_REDIRECT | No | Redirect target not allowed |
| EMPTY_RESPONSE | Yes | Upstream returned an empty response |
| UNEXPECTED_CONTENT | No | Unexpected content from upstream |
| RECORD_PARSE_ERROR | No | Failed to parse a record |
| CACHE_ERROR | No | Cache operation failed |

## Error Response Shape

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable description",
  "retryable": true | false,
  "details": { ... } | null,
  "record_position": int | null
}
```

## When Errors Occur

- **INVALID_INPUT**: query and filters both provided, or neither provided, or query exceeds max length
- **INVALID_CQL**: generated CQL is syntactically invalid
- **INVALID_URN**: URN doesn't match the `urn:lex:br:...` pattern
- **UPSTREAM_CHALLENGE**: upstream returned HTML (verification page, captcha, etc.)
- **UPSTREAM_TIMEOUT**: connect or read timeout from upstream
- **UPSTREAM_HTTP_ERROR**: non-5xx HTTP error from upstream (after retries exhausted)
- **INVALID_XML**: upstream response is not valid XML (or DTD entity expansion blocked)
- **SRU_DIAGNOSTIC**: SRU returned a diagnostic element
- **INTERNAL_ERROR**: unexpected internal failure
- **INVALID_RECORD_SCHEMA**: record_schema not in allowlist (dc, oai_dc)
- **PAYLOAD_TOO_LARGE**: request payload exceeds limit
- **RESPONSE_TOO_LARGE**: upstream response body exceeds LEXML_HTTP_MAX_RESPONSE_BYTES
- **UPSTREAM_RATE_LIMITED**: upstream returned 429
- **UNSAFE_REDIRECT**: URN redirect target host not in allowlist
- **EMPTY_RESPONSE**: upstream returned empty body
- **UNEXPECTED_CONTENT**: upstream returned unexpected content type
- **RECORD_PARSE_ERROR**: failed to parse an individual record
- **CACHE_ERROR**: cache operation failed