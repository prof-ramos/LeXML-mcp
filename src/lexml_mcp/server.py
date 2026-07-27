"""LexML MCP Server — FastMCP with 3 tools: lexml_search, lexml_resolve_urn, lexml_explain."""

from typing import Any

from lexml_mcp import config
from lexml_mcp.connectors import acervo
from lexml_mcp.models.envelope import make_envelope
from lexml_mcp.utils.cache import TTLCache

_cache = TTLCache(maxsize=config.CACHE_MAXSIZE, ttl=config.CACHE_TTL)

try:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("LexML MCP", instructions="LexML Brasil — SRU search, URN resolution, and explain.")
except ImportError:
    raise SystemExit("mcp package required: pip install mcp>=1.7.0")


# ── CQL generation from structured filters ──────────────────────────────


def _escape_cql(val: str) -> str:
    """Escape a CQL string value — double quotes inside are doubled."""
    return val.replace('"', '""')


def _build_cql_from_filters(filters: dict[str, Any]) -> str:
    """Generate a safe CQL query from structured filters.

    No string concatenation of user input — all values are escaped.
    """
    clauses: list[str] = []

    if title := filters.get("title"):
        clauses.append(f'dc.title = "{_escape_cql(title)}"')

    if terms := filters.get("terms"):
        if isinstance(terms, list) and len(terms) == 1:
            clauses.append(f'dc.subject any "{_escape_cql(terms[0])}"')
        elif isinstance(terms, list) and len(terms) > 1:
            parts = [f'dc.subject any "{_escape_cql(t)}"' for t in terms]
            clauses.append("(" + " or ".join(parts) + ")")

    if doc_type := filters.get("document_type"):
        clauses.append(f'dc.type = "{_escape_cql(doc_type)}"')

    if authority := filters.get("authority"):
        clauses.append(f'dc.creator = "{_escape_cql(authority)}"')

    if date_from := filters.get("date_from"):
        clauses.append(f'dc.date >= "{_escape_cql(date_from)}"')

    if date_to := filters.get("date_to"):
        clauses.append(f'dc.date <= "{_escape_cql(date_to)}"')

    if not clauses:
        raise ValueError("At least one filter is required")

    return " and ".join(clauses)


# ── Tools ────────────────────────────────────────────────────────────────


@mcp.tool()
async def lexml_search(
    query: str | None = None,
    start_record: int = 1,
    maximum_records: int = 10,
    record_schema: str = "dc",
    filters: dict[str, Any] | None = None,
) -> dict:
    """Search the LexML SRU acervo.

    Args:
        query: CQL query string (e.g. 'dc.title any "constituição"')
        start_record: First record position (default 1)
        maximum_records: Max records to return (default 10, max 100)
        record_schema: Record schema (default 'dc')
        filters: Structured filters {title, terms[], document_type, authority, date_from, date_to}.
                 Mutually exclusive with query. When provided, generates safe CQL.
    """
    # Validate query vs filters mutual exclusivity
    if query and filters:
        return make_envelope(
            {
                "error": True,
                "error_type": "invalid_input",
                "error_message": "query and filters are mutually exclusive",
            },
            "lexml_search",
        )
    if not query and not filters:
        return make_envelope(
            {
                "error": True,
                "error_type": "invalid_input",
                "error_message": "Either query or filters must be provided",
            },
            "lexml_search",
        )

    # Generate CQL from filters if provided
    if filters:
        try:
            query = _build_cql_from_filters(filters)
        except ValueError as e:
            return make_envelope(
                {
                    "error": True,
                    "error_type": "invalid_input",
                    "error_message": str(e),
                },
                "lexml_search",
            )

    assert query is not None  # guaranteed by mutual exclusivity check above
    maximum_records = min(maximum_records, 100)  # ponytail: server-side cap
    cache_key = f"search:{query}:{start_record}:{maximum_records}:{record_schema}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached["cache_status"] = "hit"
        return make_envelope(cached, "lexml_search")

    result = await acervo.sru_search(query, start_record, maximum_records, record_schema)

    # Never cache challenges
    if result.get("is_challenge_like"):
        result["cache_status"] = "bypassed"
        return make_envelope(result, "lexml_search")

    _cache.set(cache_key, result)
    result["cache_status"] = "miss"
    return make_envelope(result, "lexml_search")


@mcp.tool()
async def lexml_resolve_urn(urn: str) -> dict:
    """Resolve a LexML URN to its public URL.

    Args:
        urn: LexML URN (e.g. 'urn:lex:br:federal:lei:1990-09-11;8078')
    """
    cache_key = f"urn:{urn}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached["cache_status"] = "hit"
        return make_envelope(cached, "lexml_resolve_urn")

    result = await acervo.resolve_urn(urn)
    _cache.set(cache_key, result)
    result["cache_status"] = "miss"
    return make_envelope(result, "lexml_resolve_urn")


@mcp.tool()
async def lexml_explain() -> dict:
    """Retrieve metadata about the LexML SRU service (explain operation)."""
    cache_key = "explain"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached["cache_status"] = "hit"
        return make_envelope(cached, "lexml_explain")

    result = await acervo.sru_explain()

    if result.get("is_challenge_like"):
        result["cache_status"] = "bypassed"
        return make_envelope(result, "lexml_explain")

    _cache.set(cache_key, result)
    result["cache_status"] = "miss"
    return make_envelope(result, "lexml_explain")


# ── Resource ─────────────────────────────────────────────────────────────


@mcp.resource("lexml://sru/explain")
async def explain_resource() -> dict:
    """Return cached explain data from the SRU service."""
    cached = _cache.get("explain")
    if cached is not None:
        return make_envelope(cached, "lexml_explain")
    result = await acervo.sru_explain()
    if not result.get("is_challenge_like"):
        _cache.set("explain", result)
    result["cache_status"] = "miss"
    return make_envelope(result, "lexml_explain")


def main() -> None:
    """Entry point: run the MCP server via stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()