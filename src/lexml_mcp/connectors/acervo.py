"""Acervo connector — SRU search, explain, and URN resolution against LexML."""

import asyncio
import hashlib
import random
import re
import time
from typing import Any
from urllib.parse import urlparse

from defusedxml import ElementTree as ET

import httpx

from lexml_mcp import config
from lexml_mcp.models.error import StructuredError
from lexml_mcp.models.provenance import Provenance
from lexml_mcp.utils.challenge import is_challenge_html, build_challenge_object
from lexml_mcp.utils.logging import get_logger, make_request_id

logger = get_logger(__name__)

_SRU_NS = {
    "sru": "http://www.loc.gov/zing/srw/",
    "diag": "http://www.loc.gov/zing/srw/diagnostic/",
}

# URN validation — ponytail: simple regex, upgrade to full RFC 2141 if needed
_URN_PATTERN = re.compile(
    r"^urn:lex:br:[a-z]+:[a-z0-9_-]+:\d{4}-\d{2}-\d{2}(?:;\d+)?$"
)
_ALLOWED_URN_HOSTS = frozenset({"www.lexml.gov.br", "lexml.gov.br"})

_ALLOWED_RECORD_SCHEMAS = frozenset({"dc", "oai_dc"})


def validate_urn(urn: str) -> str | None:
    """Validate a LexML URN. Returns error message or None."""
    if not _URN_PATTERN.match(urn):
        return f"Invalid URN syntax: {urn}"
    return None


def validate_urn_url(url: str) -> str | None:
    """Validate the final URL after URN resolution. Returns error message or None."""
    parsed = urlparse(url)
    if parsed.hostname not in _ALLOWED_URN_HOSTS:
        return f"SSRF blocked: host {parsed.hostname} not allowed"
    return None


def validate_query(query: str) -> str | None:
    """Validate query length. Returns error message or None."""
    if len(query) > config.LEXML_QUERY_MAX_LENGTH:
        return f"Query exceeds max length ({config.LEXML_QUERY_MAX_LENGTH} chars)"
    return None


def validate_record_schema(schema: str) -> str | None:
    """Validate record schema against allowlist. Returns error message or None."""
    if schema not in _ALLOWED_RECORD_SCHEMAS:
        return f"Invalid record schema '{schema}', allowed: {', '.join(sorted(_ALLOWED_RECORD_SCHEMAS))}"
    return None


def _sanitize_excerpt(body: str, max_chars: int) -> str:
    """Strip script tags and truncate to max_chars."""
    cleaned = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.IGNORECASE | re.DOTALL)
    return cleaned[:max_chars]


def _should_retry(exc: Exception) -> bool:
    """Return True if the exception is retryable (timeout or 5xx)."""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


async def _fetch_with_retry(client: httpx.AsyncClient, url: str) -> httpx.Response:
    """Fetch with retry + jitter for transient failures."""
    max_retries = config.LEXML_HTTP_MAX_RETRIES
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp
        except httpx.TimeoutException as e:
            last_exc = e
            if attempt < max_retries:
                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.warning("retry", extra={"attempt": attempt + 1, "url": url, "delay": round(delay, 2)})
                await asyncio.sleep(delay)
                continue
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500 and attempt < max_retries:
                last_exc = e
                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.warning("retry", extra={"attempt": attempt + 1, "url": url, "delay": round(delay, 2)})
                await asyncio.sleep(delay)
                continue
            raise
    raise last_exc  # type: ignore[misc]


async def sru_search(
    query: str,
    start_record: int = 1,
    maximum_records: int = 10,
    record_schema: str = "dc",
) -> dict[str, Any]:
    """Execute a searchRetrieve operation against the LexML SRU endpoint."""
    params = {
        "operation": "searchRetrieve",
        "version": "1.2",
        "query": query,
        "startRecord": start_record,
        "maximumRecords": maximum_records,
        "recordSchema": record_schema,
    }
    url = str(httpx.URL(config.SRU_BASE_URL, params=params))
    return await _fetch_and_parse(url)


async def sru_explain() -> dict[str, Any]:
    """Execute an explain operation against the LexML SRU endpoint."""
    params = {"operation": "explain", "version": "1.2"}
    url = str(httpx.URL(config.SRU_BASE_URL, params=params))
    return await _fetch_and_parse(url)


async def resolve_urn(urn: str, verify: bool = False) -> dict[str, Any]:
    """Resolve a LexML URN to its public URL, optionally following redirects.

    When verify=False (default), only constructs the URL without following redirects.
    When verify=True, follows redirects and validates the final host (SSRF guard).

    Args:
        urn: LexML URN to resolve.
        verify: If True, follow redirects and validate final host.
    """
    # Validate URN syntax
    err = validate_urn(urn)
    if err:
        return {
            "error": True,
            "error_type": "invalid_urn",
            "error_message": err,
            "urn": urn,
        }

    url = config.URN_RESOLVE_TEMPLATE.format(urn=urn)
    provenance = Provenance.build(url=url, source_kind="urn", authority="lexml.gov.br")

    if not verify:
        # ponytail: just return the constructed URL, no network call
        return {
            "urn": urn,
            "public_url": url,
            "provenance": provenance.to_dict(),
        }

    try:
        async with httpx.AsyncClient(
            timeout=config.REQUEST_TIMEOUT, follow_redirects=False
        ) as client:
            resp = await client.get(url)
            chain = [{"url": str(resp.url), "status": resp.status_code}]
            # Follow redirect chain manually, max MAX_REDIRECTS
            redirect_count = 0
            next_url = resp.headers.get("location")
            while next_url and redirect_count < config.MAX_REDIRECTS:
                chain.append({"url": next_url, "status": 302})
                r2 = await client.get(next_url)
                chain[-1]["status"] = r2.status_code
                next_url = r2.headers.get("location")
                redirect_count += 1

            final_url = str(resp.url)

            # Validate final host (SSRF guard)
            host_err = validate_urn_url(final_url)
            if host_err:
                return {
                    "error": True,
                    "error_type": "invalid_urn",
                    "error_message": host_err,
                    "urn": urn,
                    "provenance": provenance.to_dict(),
                }

            return {
                "urn": urn,
                "public_url": final_url,
                "status_code": resp.status_code,
                "redirect_chain": chain,
                "provenance": provenance.to_dict(),
            }
    except httpx.TimeoutException:
        return {
            **StructuredError.timeout(url).to_dict(),
            "provenance": provenance.to_dict(),
        }
    except httpx.HTTPError as e:
        return {
            **StructuredError.network(str(e), url).to_dict(),
            "provenance": provenance.to_dict(),
        }


async def _fetch_and_parse(url: str) -> dict[str, Any]:
    """Fetch a URL and parse the response, handling challenges and errors."""
    request_id = make_request_id()
    start = time.monotonic()
    provenance = Provenance.build(url=url)
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                (config.LEXML_HTTP_CONNECT_TIMEOUT, config.LEXML_HTTP_READ_TIMEOUT),
            ),
            follow_redirects=True,
            max_redirects=config.MAX_REDIRECTS,
            headers={"User-Agent": config.LEXML_USER_AGENT},
        ) as client:
            resp = await _fetch_with_retry(client, url)
            body = resp.text
            ct = resp.headers.get("content-type", "")

            # Response size limit
            body_bytes = len(body.encode("utf-8"))
            if body_bytes > config.LEXML_HTTP_MAX_RESPONSE_BYTES:
                duration_ms = int((time.monotonic() - start) * 1000)
                logger.warning(
                    "response_too_large",
                    extra={
                        "request_id": request_id,
                        "duration_ms": duration_ms,
                        "status": "error",
                        "error_code": "RESPONSE_TOO_LARGE",
                        "body_bytes": body_bytes,
                    },
                )
                return {
                    "error": True,
                    "error_type": "response_too_large",
                    "error_message": f"Response too large ({body_bytes} bytes)",
                    "provenance": provenance.to_dict(),
                }

            provenance.content_hash = hashlib.sha256(body.encode()).hexdigest()[:16]
            provenance.retrieved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    except httpx.TimeoutException:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "timeout",
            extra={"request_id": request_id, "duration_ms": duration_ms, "status": "error", "error_code": "UPSTREAM_TIMEOUT"},
        )
        return {
            **StructuredError.timeout(url).to_dict(),
            "provenance": provenance.to_dict(),
        }
    except httpx.HTTPError as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "http_error",
            extra={"request_id": request_id, "duration_ms": duration_ms, "status": "error", "error_code": "UPSTREAM_HTTP_ERROR"},
        )
        return {
            **StructuredError.network(str(e), url).to_dict(),
            "provenance": provenance.to_dict(),
        }

    # Challenge detection
    if is_challenge_html(ct, body):
        challenge = build_challenge_object(resp.status_code, ct, body)
        challenge["provenance"] = provenance.to_dict()
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "challenge",
            extra={"request_id": request_id, "duration_ms": duration_ms, "status": "error", "error_code": "UPSTREAM_CHALLENGE", "challenge_detected": True},
        )
        return challenge

    # Try XML parse (defusedxml protects against entity expansion)
    try:
        root = ET.fromstring(body)
    except (ET.ParseError, Exception) as e:
        err_msg = str(e)
        if "EntitiesForbidden" in type(e).__name__ or "Forbidden" in err_msg:
            err_msg = "DTD entity expansion blocked by defusedxml"
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning(
            "invalid_xml",
            extra={"request_id": request_id, "duration_ms": duration_ms, "status": "error", "error_code": "INVALID_XML"},
        )
        return {
            **StructuredError.invalid_xml(err_msg, url).to_dict(),
            "provenance": provenance.to_dict(),
        }

    # Parse SRU searchRetrieve response
    result = _parse_sru_response(url, root, body, ct, provenance)
    duration_ms = int((time.monotonic() - start) * 1000)
    record_count = len(result.get("records", []))
    logger.info(
        "search_complete",
        extra={
            "request_id": request_id,
            "duration_ms": duration_ms,
            "status": "ok",
            "record_count": record_count,
        },
    )
    return result


def _parse_sru_response(
    url: str,
    root: Any,
    body: str,
    ct: str,
    provenance: Provenance,
) -> dict[str, Any]:
    """Parse a successful SRU XML response into a structured dict."""
    result: dict[str, Any] = {
        "request_url": url,
        "content_type": ct,
        "provenance": provenance.to_dict(),
    }

    # numberOfRecords
    nrec = root.find(".//sru:numberOfRecords", _SRU_NS)
    if nrec is not None and nrec.text:
        result["number_of_records"] = int(nrec.text)

    # nextRecordPosition
    nrp = root.find(".//sru:nextRecordPosition", _SRU_NS)
    if nrp is not None and nrp.text:
        result["next_record_position"] = int(nrp.text)

    # Records
    records = []
    for rec in root.findall(".//sru:record", _SRU_NS):
        pos_el = rec.find("sru:recordPosition", _SRU_NS)
        schema_el = rec.find("sru:recordSchema", _SRU_NS)
        data_el = rec.find("sru:recordData", _SRU_NS)
        rec_data: dict[str, Any] = {}
        field_values: dict[str, list[str]] = {}
        if data_el is not None:
            for child in data_el.iter():
                if child == data_el:
                    continue
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                val = child.text or ""
                # field_values: always list, preserves repeats
                field_values.setdefault(tag, []).append(val)
                # data: backward compat (first value as scalar, repeats as list)
                if tag in rec_data:
                    if not isinstance(rec_data[tag], list):
                        rec_data[tag] = [rec_data[tag]]
                    rec_data[tag].append(val)
                else:
                    rec_data[tag] = val
        records.append(
            {
                "record_position": int(pos_el.text) if pos_el is not None and pos_el.text else 0,
                "record_schema": (schema_el.text or "dc") if schema_el is not None else "dc",
                "data": rec_data,
                "field_values": field_values,
            }
        )
    result["records"] = records

    # Diagnostics
    diags = []
    for d in root.findall(".//diag:diagnostic", _SRU_NS):
        uri = d.find("diag:uri", _SRU_NS)
        msg = d.find("diag:message", _SRU_NS)
        diags.append(
            {
                "uri": uri.text if uri is not None else "",
                "message": msg.text if msg is not None else "",
            }
        )
    result["diagnostics"] = diags

    # Debug raw responses
    if config.LEXML_DEBUG_RAW_RESPONSES:
        result["raw_excerpt"] = _sanitize_excerpt(body, config.LEXML_RAW_EXCERPT_MAX_CHARS)

    return result