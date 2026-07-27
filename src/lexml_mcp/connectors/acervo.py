"""Acervo connector — SRU search, explain, and URN resolution against LexML."""

import re
from typing import Any
from urllib.parse import urlparse

from defusedxml import ElementTree as ET

import httpx

from lexml_mcp import config
from lexml_mcp.models.error import StructuredError
from lexml_mcp.models.provenance import Provenance
from lexml_mcp.utils.challenge import is_challenge_html, build_challenge_object

_SRU_NS = {
    "sru": "http://www.loc.gov/zing/srw/",
    "diag": "http://www.loc.gov/zing/srw/diagnostic/",
}

# URN validation — ponytail: simple regex, upgrade to full RFC 2141 if needed
_URN_PATTERN = re.compile(
    r"^urn:lex:br:[a-z]+:[a-z0-9_-]+:\d{4}-\d{2}-\d{2}(?:;\d+)?$"
)
_ALLOWED_URN_HOSTS = frozenset({"www.lexml.gov.br", "lexml.gov.br"})


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


async def resolve_urn(urn: str) -> dict[str, Any]:
    """Resolve a LexML URN to its public URL, following redirects.

    Validates URN syntax and final host to prevent SSRF.
    Limits redirect chain to MAX_REDIRECTS (default 5).
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
    provenance = Provenance.build(url=url)
    try:
        async with httpx.AsyncClient(
            timeout=config.REQUEST_TIMEOUT,
            follow_redirects=True,
            max_redirects=config.MAX_REDIRECTS,
        ) as client:
            resp = await client.get(url)
            body = resp.text
            ct = resp.headers.get("content-type", "")
            provenance.content_hash = (
                __import__("hashlib").sha256(body.encode()).hexdigest()[:16]
            )
            provenance.retrieved_at = __import__(
                "time"
            ).strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime())
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

    # Challenge detection
    if is_challenge_html(ct, body):
        challenge = build_challenge_object(resp.status_code, ct, body)
        return {
            **challenge,
            "provenance": provenance.to_dict(),
        }

    # Try XML parse (defusedxml protects against entity expansion)
    try:
        root = ET.fromstring(body)
    except (ET.ParseError, Exception) as e:
        err_msg = str(e)
        if "EntitiesForbidden" in type(e).__name__ or "Forbidden" in err_msg:
            err_msg = "DTD entity expansion blocked by defusedxml"
        return {
            **StructuredError.invalid_xml(err_msg, url).to_dict(),
            "provenance": provenance.to_dict(),
        }

    # Parse SRU searchRetrieve response
    return _parse_sru_response(url, root, body, ct, provenance)


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
        if data_el is not None:
            # Flatten child elements into a dict
            for child in data_el.iter():
                if child == data_el:
                    continue
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag in rec_data:
                    if not isinstance(rec_data[tag], list):
                        rec_data[tag] = [rec_data[tag]]
                    rec_data[tag].append(child.text or "")
                else:
                    rec_data[tag] = child.text or ""
        records.append(
            {
                "record_position": int(pos_el.text) if pos_el is not None and pos_el.text else 0,
                "record_schema": (schema_el.text or "dc") if schema_el is not None else "dc",
                "data": rec_data,
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

    return result