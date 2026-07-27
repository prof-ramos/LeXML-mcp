# Security

## Implemented measures

### SSRF protection

- **URN resolution host allowlist**: `validate_urn_url()` checks the final resolved host against `_ALLOWED_URN_HOSTS = frozenset({"www.lexml.gov.br", "lexml.gov.br"})`. Any redirect to an unexpected host is blocked at the data layer before returning to the client.
- **No user-controlled URLs**: The only URL the server builds is from config values (`LEXML_SRU_URL` and `LEXML_URN_TEMPLATE`). User input (queries, URNs) is interpolated into parameter positions, never into the URL host or path.
- **Redirect chain limits**: `MAX_REDIRECTS` (default 5) caps the number of hops followed during URN resolution.

### XML parsing

- **defusedxml**: All SRU XML responses are parsed with `defusedxml.ElementTree`, which blocks entity expansion (billion laughs), external entity references (XXE), and DTD-based attacks.
- **DTD entity detection**: When `defusedxml` raises `EntitiesForbidden`, the error is caught and returned as a structured `invalid_xml` error — no crash, no exposure.

### URN validation

- **Regex-based syntax check**: `_URN_PATTERN` validates that URNs match the expected LexML format (`urn:lex:br:<authority>:<collection>:<date>[;<id>]`). Malformed URNs are rejected before any network call.

### Challenge detection

- **Content-type heuristics**: HTML content-type or HTML-looking bodies (doctype, `<html>`, challenge keywords like "verificação de segurança") are detected before XML parsing, preventing downstream processing of non-XML responses.
- **Challenges never cached**: `is_challenge_like` responses bypass the cache to avoid serving stale challenge pages as successes.

### Untrusted content

- **Content hash**: Every response carries a SHA-256 content hash (first 16 hex chars) in the provenance envelope for integrity verification by downstream consumers.
- **No eval / exec**: The server never evaluates dynamically-generated code or templates.

## Known limitations

| Area | Limitation |
|------|-----------|
| **Transport** | stdio only. No TLS or authentication between MCP client and server — rely on the client's security boundary. |
| **SSRF scope** | Host allowlist covers only the URN resolution path. The SRU endpoint URL is configurable via `LEXML_SRU_URL` — if an attacker controls the environment, they can redirect the SRU connector. Assume the env is trusted. |
| **Unicode normalization** | Content is served as-is. No NFC/NFKC normalization. Callers should normalize if comparing identifiers. |
| **No output sanitization** | Raw SRU data (titles, subjects, authors) is returned verbatim. Consumers should sanitize for their display context (e.g., HTML-escape before rendering in a browser). |
| **No rate limiting** | The server does not rate-limit requests. The upstream SRU endpoint may throttle independently. |
| **No audit log** | All provenance is per-response metadata; no persistent event log exists. |