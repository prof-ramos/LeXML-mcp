"""Offline tests for LexML MCP — fixtures cover SRU success, challenge, invalid XML, explain."""

import json
import os
from unittest.mock import AsyncMock, patch

import pytest

from lexml_mcp.connectors.acervo import (
    _parse_sru_response,
    is_challenge_html,
    build_challenge_object,
    validate_urn,
)
from lexml_mcp.models.error import StructuredError, ErrorCode, error_code_to_dict
from lexml_mcp.models.envelope import make_envelope
from lexml_mcp.models.provenance import Provenance
from lexml_mcp.utils.cache import TTLCache

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name: str) -> str:
    with open(os.path.join(FIXTURES, name)) as f:
        return f.read()


# ── Keep all existing test classes (they must still pass) ────────────────


class TestChallengeDetection:
    def test_html_content_type(self):
        assert is_challenge_html("text/html", "<html></html>") is True

    def test_xml_with_html_body(self):
        assert is_challenge_html("application/xml", "<!DOCTYPE html>") is True

    def test_xml_with_security_check_keywords(self):
        assert (
            is_challenge_html(
                "application/xml", "Verificação de Segurança — Senado Federal"
            )
            is True
        )

    def test_clean_xml_not_challenge(self):
        assert (
            is_challenge_html(
                "application/xml",
                '<?xml version="1.0"?><searchRetrieveResponse/>',
            )
            is False
        )

    def test_build_challenge_object(self):
        obj = build_challenge_object(200, "text/html", "<html>test</html>")
        assert obj["is_challenge_like"] is True
        assert obj["content_type"] == "text/html"
        assert obj["status_code"] == 200
        assert "test" in obj["raw_excerpt"]


class TestSRUParsing:
    def test_parse_sru_success(self):
        body = _load("sru_success.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        assert result["number_of_records"] == 42
        assert result["next_record_position"] == 11
        assert len(result["records"]) == 2
        assert result["records"][0]["data"]["title"] == "Código de Defesa do Consumidor"
        assert result["records"][1]["data"]["title"] == "Constituição da República Federativa do Brasil de 1988"
        assert "provenance" in result

    def test_parse_sru_explain(self):
        body = _load("explain.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU/explain", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU/explain", root, body, "application/xml", provenance
        )
        assert "provenance" in result
        # Explain has a record with explain schema
        assert len(result["records"]) == 1
        assert result["records"][0]["record_schema"] == "http://explain.z3950.org/dtd/2.0/"

    def test_parse_invalid_xml_raises(self):
        body = _load("invalid.xml")
        from defusedxml import ElementTree as ET
        with pytest.raises(ET.ParseError):
            ET.fromstring(body)


class TestChallengeHTML:
    def test_challenge_html_detection(self):
        body = _load("challenge.html")
        assert is_challenge_html("text/html", body) is True
        obj = build_challenge_object(200, "text/html", body)
        assert obj["is_challenge_like"] is True
        assert "Verificação" in obj["raw_excerpt"]


class TestStructuredError:
    def test_network_error(self):
        err = StructuredError.network("connection refused", "http://example.com")
        d = err.to_dict()
        assert d["error"] is True
        assert d["error_type"] == "network_error"
        assert d["details"]["url"] == "http://example.com"

    def test_timeout_error(self):
        err = StructuredError.timeout("http://example.com")
        d = err.to_dict()
        assert d["error_type"] == "timeout"
        assert d["error_message"] == "Request timed out"

    def test_invalid_xml_error(self):
        err = StructuredError.invalid_xml("not well-formed", "http://example.com")
        d = err.to_dict()
        assert d["error_type"] == "invalid_xml"

    def test_http_error(self):
        err = StructuredError.http_error(503, "http://example.com")
        d = err.to_dict()
        assert d["error_type"] == "http_error"
        assert d["details"]["status_code"] == 503


class TestProvenance:
    def test_build_provenance(self):
        prov = Provenance.build(url="http://example.com", body="hello")
        d = prov.to_dict()
        assert d["source_url"] == "http://example.com"
        assert d["source_kind"] == "sru"
        assert d["authority"] == "lexml.gov.br"
        assert d["backend_name"] == "lexml-mcp"
        assert d["backend_version"] == "0.2.0"
        assert d["schema_version"] == "1.0"
        assert d["retrieved_at"] is not None
        assert d["content_hash"] is not None

    def test_provenance_no_body(self):
        prov = Provenance.build(url="http://example.com")
        d = prov.to_dict()
        assert d["content_hash"] is not None  # sha256 of empty string


class TestTTLCache:
    def test_set_and_get(self):
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key1", {"value": 42})
        assert cache.get("key1") == {"value": 42}

    def test_miss(self):
        cache = TTLCache(maxsize=10, ttl=60)
        assert cache.get("nonexistent") is None

    def test_expiry(self):
        cache = TTLCache(maxsize=10, ttl=-1)  # already expired
        cache.set("key1", "val")
        assert cache.get("key1") is None

    def test_lru_eviction(self):
        cache = TTLCache(maxsize=2, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # should evict 'a'
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_invalidate(self):
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key1", "val")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None


# ── Integration tests via connector ─────────────────────────────────────


class TestServerTools:
    """Integration tests that mock httpx to use offline fixtures."""

    @pytest.mark.asyncio
    async def test_lexml_search_success(self):
        """Mock a successful SRU search response."""
        body = _load("sru_success.xml")
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/xml"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import sru_search

            result = await sru_search(query="dc.title any 'test'")
            assert result["number_of_records"] == 42
            assert len(result["records"]) == 2
            assert "provenance" in result
            assert result["provenance"]["source_kind"] == "sru"

    @pytest.mark.asyncio
    async def test_lexml_search_challenge(self):
        """Mock a challenge HTML response."""
        body = _load("challenge.html")
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import sru_search

            result = await sru_search(query="dc.title any 'test'")
            assert result["is_challenge_like"] is True
            assert "provenance" in result

    @pytest.mark.asyncio
    async def test_lexml_search_invalid_xml(self):
        """Mock a response with malformed XML."""
        body = _load("invalid.xml")
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/xml"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import sru_search

            result = await sru_search(query="dc.title any 'test'")
            assert result["error"] is True
            assert result["error_type"] == "invalid_xml"
            assert "provenance" in result

    @pytest.mark.asyncio
    async def test_lexml_search_timeout(self):
        """Mock a timeout."""
        with patch(
            "httpx.AsyncClient.get",
            new=AsyncMock(side_effect=__import__("httpx").TimeoutException("timeout")),
        ):
            from lexml_mcp.connectors.acervo import sru_search

            result = await sru_search(query="dc.title any 'test'")
            assert result["error"] is True
            assert result["error_type"] == "timeout"
            assert "provenance" in result

    @pytest.mark.asyncio
    async def test_lexml_explain_success(self):
        """Mock a successful explain response."""
        body = _load("explain.xml")
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/xml"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import sru_explain

            result = await sru_explain()
            assert "provenance" in result
            assert len(result["records"]) == 1

    @pytest.mark.asyncio
    async def test_lexml_resolve_urn(self):
        """Mock a URN resolution."""
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://www.lexml.gov.br/urn/urn:lex:br:federal:lei:1990-09-11;8078"
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.text = "<html>ok</html>"

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import resolve_urn

            result = await resolve_urn("urn:lex:br:federal:lei:1990-09-11;8078", verify=True)
            assert result["urn"] == "urn:lex:br:federal:lei:1990-09-11;8078"
            assert result["status_code"] == 200
            assert "provenance" in result

    @pytest.mark.asyncio
    async def test_lexml_resolve_urn_no_verify(self):
        """URN resolution without verify — no network call."""
        from lexml_mcp.connectors.acervo import resolve_urn

        result = await resolve_urn("urn:lex:br:federal:lei:1990-09-11;8078", verify=False)
        assert result["urn"] == "urn:lex:br:federal:lei:1990-09-11;8078"
        assert "public_url" in result
        assert result["public_url"] == "https://www.lexml.gov.br/urn/urn:lex:br:federal:lei:1990-09-11;8078"
        assert "provenance" in result
        # No network call, so no status_code
        assert "status_code" not in result

    @pytest.mark.asyncio
    async def test_lexml_resolve_urn_timeout(self):
        """Mock a URN resolution timeout."""
        with patch(
            "httpx.AsyncClient.get",
            new=AsyncMock(side_effect=__import__("httpx").TimeoutException("timeout")),
        ):
            from lexml_mcp.connectors.acervo import resolve_urn

            result = await resolve_urn("urn:lex:br:federal:lei:1990-09-11;8078", verify=True)
            assert result["error"] is True
            assert result["error_type"] == "timeout"
            assert "provenance" in result

    # ── New fixture-based tests ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_search_no_records(self):
        """Mock a search returning zero records."""
        body = _load("sru_no_records.xml")
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/xml"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import sru_search

            result = await sru_search(query="dc.title any 'nonexistent'")
            assert result["number_of_records"] == 0
            assert len(result["records"]) == 0
            assert "provenance" in result

    @pytest.mark.asyncio
    async def test_search_403(self):
        """Mock an HTTP 403 response (HTML challenge-like)."""
        body = _load("sru_403.html")
        mock_resp = AsyncMock()
        mock_resp.status_code = 403
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import sru_search

            result = await sru_search(query="dc.title any 'test'")
            assert result["is_challenge_like"] is True
            assert "provenance" in result

    @pytest.mark.asyncio
    async def test_search_429(self):
        """Mock an HTTP 429 response."""
        body = _load("sru_429.html")
        mock_resp = AsyncMock()
        mock_resp.status_code = 429
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import sru_search

            result = await sru_search(query="dc.title any 'test'")
            assert result["is_challenge_like"] is True
            assert "provenance" in result

    @pytest.mark.asyncio
    async def test_search_500(self):
        """Mock an HTTP 500 response."""
        body = _load("sru_500.html")
        mock_resp = AsyncMock()
        mock_resp.status_code = 500
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import sru_search

            result = await sru_search(query="dc.title any 'test'")
            assert result["is_challenge_like"] is True
            assert "provenance" in result

    @pytest.mark.asyncio
    async def test_dtd_entity_expansion(self):
        """Mock a response with DTD entity — defusedxml must raise."""
        body = _load("sru_dtd.xml")
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/xml"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.connectors.acervo import sru_search

            result = await sru_search(query="dc.title any 'test'")
            # defusedxml blocks DTD entity expansion → returns invalid_xml error
            assert result["error"] is True
            assert result["error_type"] == "invalid_xml"


# ── New tests: Envelope ────────────────────────────────────────────────


class TestEnvelope:
    def test_envelope_success(self):
        result = {"number_of_records": 10, "records": [], "provenance": {"source": "test"}}
        env = make_envelope(result, "lexml_search")
        assert env["success"] is True
        assert env["partial_success"] is False
        assert env["operation"] == "lexml_search"
        assert env["schema_version"] == "1.0"
        assert env["data"]["number_of_records"] == 10
        assert env["errors"] == []
        assert env["provenance"]["source"] == "test"

    def test_envelope_error(self):
        result = {
            "error": True,
            "error_type": "timeout",
            "error_message": "Request timed out",
            "provenance": {"source": "test"},
        }
        env = make_envelope(result, "lexml_resolve_urn")
        assert env["success"] is False
        assert env["partial_success"] is False
        assert env["operation"] == "lexml_resolve_urn"
        assert len(env["errors"]) == 1
        assert env["errors"][0]["code"] == "UPSTREAM_TIMEOUT"
        assert env["errors"][0]["retryable"] is True
        assert env["data"] is None

    def test_envelope_challenge(self):
        result = {
            "is_challenge_like": True,
            "status_code": 200,
            "provenance": {"source": "test"},
        }
        env = make_envelope(result, "lexml_search")
        assert env["success"] is False
        assert len(env["errors"]) == 1
        assert env["errors"][0]["code"] == "UPSTREAM_CHALLENGE"
        assert env["errors"][0]["retryable"] is True

    def test_envelope_with_diagnostics(self):
        result = {
            "number_of_records": 5,
            "records": [],
            "diagnostics": [{"uri": "info:srw/diag/1", "message": "warn"}],
            "provenance": {"source": "test"},
        }
        env = make_envelope(result, "lexml_search")
        assert env["success"] is True
        assert env["partial_success"] is True
        assert len(env["diagnostics"]) == 1

    def test_envelope_network_error_mapping(self):
        result = {
            "error": True,
            "error_type": "network_error",
            "error_message": "connection refused",
            "provenance": {"source": "test"},
        }
        env = make_envelope(result, "lexml_search")
        assert env["errors"][0]["code"] == "UPSTREAM_HTTP_ERROR"
        assert env["errors"][0]["retryable"] is True

    def test_envelope_invalid_xml_mapping(self):
        result = {
            "error": True,
            "error_type": "invalid_xml",
            "error_message": "not well-formed",
            "provenance": {"source": "test"},
        }
        env = make_envelope(result, "lexml_search")
        assert env["errors"][0]["code"] == "INVALID_XML"
        assert env["errors"][0]["retryable"] is False


# ── New tests: Error codes ─────────────────────────────────────────────


class TestErrorCodes:
    def test_error_code_defaults(self):
        ec = ErrorCode("TEST_CODE", "test message")
        d = ec.to_dict()
        assert d["code"] == "TEST_CODE"
        assert d["message"] == "test message"
        assert d["retryable"] is False
        assert "details" not in d
        assert "record_position" not in d

    def test_error_code_with_details(self):
        d = error_code_to_dict(
            ErrorCode("INVALID_INPUT", "bad input", retryable=False),
            details={"field": "query"},
            record_position=3,
        )
        assert d["code"] == "INVALID_INPUT"
        assert d["details"]["field"] == "query"
        assert d["record_position"] == 3

    def test_error_code_retryable(self):
        ec = ErrorCode("UPSTREAM_TIMEOUT", "timeout", retryable=True)
        assert ec.to_dict()["retryable"] is True

    def test_predefined_error_codes_have_correct_retryable(self):
        from lexml_mcp.models.error import (
            INVALID_INPUT, INVALID_CQL, INVALID_URN,
            UPSTREAM_CHALLENGE, UPSTREAM_TIMEOUT, UPSTREAM_HTTP_ERROR,
            INVALID_XML, SRU_DIAGNOSTIC, INTERNAL_ERROR,
        )
        assert INVALID_INPUT.retryable is False
        assert UPSTREAM_TIMEOUT.retryable is True
        assert UPSTREAM_HTTP_ERROR.retryable is True
        assert INVALID_XML.retryable is False
        assert INTERNAL_ERROR.retryable is False
        assert SRU_DIAGNOSTIC.retryable is False


# ── New tests: URN validation ───────────────────────────────────────────


class TestURNValidation:
    def test_valid_urn(self):
        assert validate_urn("urn:lex:br:federal:lei:1990-09-11;8078") is None

    def test_valid_urn_without_semicolon(self):
        # URNs without ;id are also valid per the pattern
        assert validate_urn("urn:lex:br:federal:lei:1990-09-11") is None

    def test_invalid_urn_prefix(self):
        err = validate_urn("urn:oasis:br:federal:lei:1990-09-11")
        assert err is not None
        assert "Invalid" in err

    def test_invalid_urn_no_date(self):
        err = validate_urn("urn:lex:br:federal:lei:invalid")
        assert err is not None

    def test_invalid_urn_empty(self):
        err = validate_urn("")
        assert err is not None

    def test_validate_urn_url_allowed(self):
        from lexml_mcp.connectors.acervo import validate_urn_url
        assert validate_urn_url("https://www.lexml.gov.br/urn/123") is None

    def test_validate_urn_url_blocked(self):
        from lexml_mcp.connectors.acervo import validate_urn_url
        err = validate_urn_url("https://evil.com/urn/123")
        assert err is not None
        assert "SSRF" in err


# ── New tests: CQL generation ───────────────────────────────────────────


class TestCQLGeneration:
    def test_single_term(self):
        from lexml_mcp.server import _build_cql_from_filters
        cql = _build_cql_from_filters({"terms": ["constituição"]})
        assert 'dc.subject any "constituição"' in cql

    def test_multiple_terms(self):
        from lexml_mcp.server import _build_cql_from_filters
        cql = _build_cql_from_filters({"terms": ["lei", "decreto"]})
        assert "(dc.subject any" in cql
        assert "lei" in cql
        assert "decreto" in cql
        assert "or" in cql

    def test_title_filter(self):
        from lexml_mcp.server import _build_cql_from_filters
        cql = _build_cql_from_filters({"title": "Constituição"})
        assert 'dc.title = "Constituição"' in cql

    def test_authority_filter(self):
        from lexml_mcp.server import _build_cql_from_filters
        cql = _build_cql_from_filters({"authority": "federal"})
        assert 'dc.creator = "federal"' in cql

    def test_date_range(self):
        from lexml_mcp.server import _build_cql_from_filters
        cql = _build_cql_from_filters({"date_from": "2020-01-01", "date_to": "2020-12-31"})
        assert 'dc.date >= "2020-01-01"' in cql
        assert 'dc.date <= "2020-12-31"' in cql
        assert " and " in cql

    def test_full_filter(self):
        from lexml_mcp.server import _build_cql_from_filters
        cql = _build_cql_from_filters({
            "title": "Test",
            "authority": "federal",
            "document_type": "lei",
        })
        assert 'dc.title = "Test"' in cql
        assert 'dc.creator = "federal"' in cql
        assert 'dc.type = "lei"' in cql

    def test_empty_filters_raises(self):
        from lexml_mcp.server import _build_cql_from_filters
        with pytest.raises(ValueError, match="At least one filter"):
            _build_cql_from_filters({})

    def test_cql_injection_escaped(self):
        from lexml_mcp.server import _build_cql_from_filters
        # Double-quote injection attempt
        cql = _build_cql_from_filters({"title": 'test" or dc.title any "evil'})
        # The injected quote should be doubled, not closing the string
        assert '"" or dc.title any ""' in cql or '"test"" or dc.title any ""evil"' in cql


# ── New tests: Resource ────────────────────────────────────────────────


class TestResource:
    @pytest.mark.asyncio
    async def test_explain_resource_returns_envelope(self):
        """The explain resource should return an envelope with cached explain data."""
        body = _load("explain.xml")
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/xml"}
        mock_resp.text = body

        with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
            from lexml_mcp.server import explain_resource

            result = await explain_resource()
            # Must return an envelope
            assert "success" in result
            assert "operation" in result
            assert result["operation"] == "lexml_explain"
            assert result["success"] is True
            assert "data" in result


# ── Server registration ────────────────────────────────────────────────


class TestServerRegistration:
    def test_three_tools_registered(self):
        from lexml_mcp.server import mcp

        tools = mcp._tool_manager._tools
        assert len(tools) == 3
        tool_names = set(tools)
        assert tool_names == {"lexml_search", "lexml_resolve_urn", "lexml_explain"}

    def test_resource_registered(self):
        from lexml_mcp.server import mcp

        resources = mcp._resource_manager._resources
        assert "lexml://sru/explain" in resources


# ── New tests: field_values ────────────────────────────────────────────


class TestFieldValues:
    def test_field_values_in_parse(self):
        """field_values is a dict[str, list[str]] alongside data."""
        body = _load("sru_success.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        for rec in result["records"]:
            assert "field_values" in rec
            assert isinstance(rec["field_values"], dict)
            for key, vals in rec["field_values"].items():
                assert isinstance(vals, list)
                assert len(vals) >= 1
            # data still present for backward compat
            assert "data" in rec

    def test_field_values_multi_title(self):
        """sru_multi_title has 2 titles in field_values."""
        body = _load("sru_multi_title.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        assert len(result["records"]) == 1
        fv = result["records"][0]["field_values"]
        assert fv["title"] == ["Lei Principal", "Lei Alterada"]

    def test_field_values_multi_id(self):
        """sru_multi_id has 2 identifiers in field_values."""
        body = _load("sru_multi_id.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        assert len(result["records"]) == 1
        fv = result["records"][0]["field_values"]
        assert len(fv["identifier"]) == 2


# ── New tests: New error codes ─────────────────────────────────────────


class TestNewErrorCodes:
    def test_invalid_record_schema_exists(self):
        from lexml_mcp.models.error import INVALID_RECORD_SCHEMA
        assert INVALID_RECORD_SCHEMA.code == "INVALID_RECORD_SCHEMA"
        assert INVALID_RECORD_SCHEMA.retryable is False

    def test_payload_too_large_exists(self):
        from lexml_mcp.models.error import PAYLOAD_TOO_LARGE
        assert PAYLOAD_TOO_LARGE.code == "PAYLOAD_TOO_LARGE"

    def test_response_too_large_exists(self):
        from lexml_mcp.models.error import RESPONSE_TOO_LARGE
        assert RESPONSE_TOO_LARGE.code == "RESPONSE_TOO_LARGE"

    def test_upstream_rate_limited_exists(self):
        from lexml_mcp.models.error import UPSTREAM_RATE_LIMITED
        assert UPSTREAM_RATE_LIMITED.code == "UPSTREAM_RATE_LIMITED"
        assert UPSTREAM_RATE_LIMITED.retryable is True

    def test_unsafe_redirect_exists(self):
        from lexml_mcp.models.error import UNSAFE_REDIRECT
        assert UNSAFE_REDIRECT.code == "UNSAFE_REDIRECT"

    def test_empty_response_exists(self):
        from lexml_mcp.models.error import EMPTY_RESPONSE
        assert EMPTY_RESPONSE.code == "EMPTY_RESPONSE"
        assert EMPTY_RESPONSE.retryable is True

    def test_unexpected_content_exists(self):
        from lexml_mcp.models.error import UNEXPECTED_CONTENT
        assert UNEXPECTED_CONTENT.code == "UNEXPECTED_CONTENT"

    def test_record_parse_error_exists(self):
        from lexml_mcp.models.error import RECORD_PARSE_ERROR
        assert RECORD_PARSE_ERROR.code == "RECORD_PARSE_ERROR"

    def test_cache_error_exists(self):
        from lexml_mcp.models.error import CACHE_ERROR
        assert CACHE_ERROR.code == "CACHE_ERROR"

    def test_all_18_error_codes(self):
        from lexml_mcp.models.error import (
            INVALID_INPUT, INVALID_CQL, INVALID_URN,
            UPSTREAM_CHALLENGE, UPSTREAM_TIMEOUT, UPSTREAM_HTTP_ERROR,
            INVALID_XML, SRU_DIAGNOSTIC, INTERNAL_ERROR,
            INVALID_RECORD_SCHEMA, PAYLOAD_TOO_LARGE, RESPONSE_TOO_LARGE,
            UPSTREAM_RATE_LIMITED, UNSAFE_REDIRECT, EMPTY_RESPONSE,
            UNEXPECTED_CONTENT, RECORD_PARSE_ERROR, CACHE_ERROR,
        )
        codes = [
            INVALID_INPUT, INVALID_CQL, INVALID_URN,
            UPSTREAM_CHALLENGE, UPSTREAM_TIMEOUT, UPSTREAM_HTTP_ERROR,
            INVALID_XML, SRU_DIAGNOSTIC, INTERNAL_ERROR,
            INVALID_RECORD_SCHEMA, PAYLOAD_TOO_LARGE, RESPONSE_TOO_LARGE,
            UPSTREAM_RATE_LIMITED, UNSAFE_REDIRECT, EMPTY_RESPONSE,
            UNEXPECTED_CONTENT, RECORD_PARSE_ERROR, CACHE_ERROR,
        ]
        assert len(codes) == 18


# ── New tests: Logging ─────────────────────────────────────────────────


class TestLogging:
    def test_get_logger(self):
        from lexml_mcp.utils.logging import get_logger
        log = get_logger("test")
        assert log.name == "test"
        # Logger level is NOTSET (0) by default, effective level is WARNING
        assert log.getEffectiveLevel() > 0

    def test_make_request_id(self):
        from lexml_mcp.utils.logging import make_request_id
        rid = make_request_id()
        assert isinstance(rid, str)
        assert len(rid) == 12

    def test_json_formatter(self):
        from lexml_mcp.utils.logging import JsonFormatter
        import logging
        fmt = JsonFormatter()
        rec = logging.LogRecord("test", logging.INFO, "", 0, "hello", (), None)
        out = fmt.format(rec)
        assert '"message": "hello"' in out
        assert '"level": "INFO"' in out


# ── New tests: Query validation ────────────────────────────────────────


class TestQueryValidation:
    def test_validate_query_ok(self):
        from lexml_mcp.connectors.acervo import validate_query
        assert validate_query("dc.title any 'test'") is None

    def test_validate_query_too_long(self):
        from lexml_mcp.connectors.acervo import validate_query
        long_q = "x" * 5000
        err = validate_query(long_q)
        assert err is not None
        assert "max length" in err

    def test_validate_record_schema_ok(self):
        from lexml_mcp.connectors.acervo import validate_record_schema
        assert validate_record_schema("dc") is None
        assert validate_record_schema("oai_dc") is None

    def test_validate_record_schema_invalid(self):
        from lexml_mcp.connectors.acervo import validate_record_schema
        err = validate_record_schema("marc21")
        assert err is not None
        assert "marc21" in err


# ── New tests: Response size limit ─────────────────────────────────────


class TestResponseSizeLimit:
    @pytest.mark.asyncio
    async def test_response_too_large(self):
        """Mock a response that exceeds the size limit."""
        # Temporarily lower the limit
        import lexml_mcp.config as cfg
        original = cfg.LEXML_HTTP_MAX_RESPONSE_BYTES
        cfg.LEXML_HTTP_MAX_RESPONSE_BYTES = 10
        try:
            mock_resp = AsyncMock()
            mock_resp.status_code = 200
            mock_resp.headers = {"content-type": "application/xml"}
            mock_resp.text = "x" * 100  # > 10 bytes

            with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=mock_resp)):
                from lexml_mcp.connectors.acervo import sru_search
                result = await sru_search(query="dc.title any 'test'")
                assert result["error"] is True
                assert result["error_type"] == "response_too_large"
        finally:
            cfg.LEXML_HTTP_MAX_RESPONSE_BYTES = original


# ── New tests: Retries ─────────────────────────────────────────────────


class TestRetries:
    def test_should_retry_timeout(self):
        from lexml_mcp.connectors.acervo import _should_retry
        assert _should_retry(__import__("httpx").TimeoutException("timeout")) is True

    def test_should_retry_5xx(self):
        from lexml_mcp.connectors.acervo import _should_retry
        import httpx
        resp = httpx.Response(503)
        exc = httpx.HTTPStatusError("503", request=httpx.Request("GET", "http://x.com"), response=resp)
        assert _should_retry(exc) is True

    def test_should_not_retry_4xx(self):
        from lexml_mcp.connectors.acervo import _should_retry
        import httpx
        resp = httpx.Response(400)
        exc = httpx.HTTPStatusError("400", request=httpx.Request("GET", "http://x.com"), response=resp)
        assert _should_retry(exc) is False


# ── New tests: Debug raw responses ─────────────────────────────────────


class TestDebugRaw:
    def test_sanitize_excerpt_strips_scripts(self):
        from lexml_mcp.connectors.acervo import _sanitize_excerpt
        body = "<root><script>alert('xss')</script>safe</root>"
        out = _sanitize_excerpt(body, 100)
        assert "alert" not in out
        assert "safe" in out

    def test_sanitize_excerpt_truncates(self):
        from lexml_mcp.connectors.acervo import _sanitize_excerpt
        out = _sanitize_excerpt("x" * 200, 50)
        assert len(out) == 50


# ── New tests: New fixtures ────────────────────────────────────────────


class TestNewFixtures:
    def test_sru_namespace_parses(self):
        body = _load("sru_namespace.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        assert len(result["records"]) == 1
        assert "custom" in result["records"][0]["data"]

    def test_sru_unknown_parses(self):
        body = _load("sru_unknown.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        assert len(result["records"]) == 1
        assert result["records"][0]["data"].get("unknownField") == "valor inesperado"

    def test_sru_deep_parses(self):
        body = _load("sru_deep.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        assert len(result["records"]) == 1
        # Deep nested elements get flattened
        assert "nested" in result["records"][0]["data"]

    def test_sru_diag_fatal(self):
        body = _load("sru_diag_fatal.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        assert len(result["diagnostics"]) == 1
        assert "Query syntax error" in result["diagnostics"][0]["message"]

    def test_sru_diag_nonfatal(self):
        body = _load("sru_diag_nonfatal.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        assert len(result["diagnostics"]) == 1
        assert len(result["records"]) == 1
        assert result["number_of_records"] == 5

    def test_empty_response_parses(self):
        body = _load("empty_response.xml")
        from defusedxml import ElementTree as ET
        root = ET.fromstring(body)
        provenance = Provenance.build(url="https://example.com/SRU", body=body)
        result = _parse_sru_response(
            "https://example.com/SRU", root, body, "application/xml", provenance
        )
        assert result["number_of_records"] == 0
        assert len(result["records"]) == 0


# ── New tests: Config ──────────────────────────────────────────────────


class TestNewConfig:
    def test_new_config_values_exist(self):
        import lexml_mcp.config as cfg
        assert cfg.LEXML_HTTP_CONNECT_TIMEOUT == 5.0
        assert cfg.LEXML_HTTP_READ_TIMEOUT == 20.0
        assert cfg.LEXML_HTTP_MAX_RESPONSE_BYTES == 5242880
        assert cfg.LEXML_HTTP_MAX_RETRIES == 2
        assert cfg.LEXML_QUERY_MAX_LENGTH == 4096
        assert cfg.LEXML_MAXIMUM_RECORDS_LIMIT == 50
        assert cfg.LEXML_DEBUG_RAW_RESPONSES is False
        assert cfg.LEXML_RAW_EXCERPT_MAX_CHARS == 1024
        assert cfg.LEXML_LOG_LEVEL == "INFO"
        assert cfg.LEXML_USER_AGENT == "lexml-mcp/0.2.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
