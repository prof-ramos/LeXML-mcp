"""Centralized configuration for LexML MCP."""

import os


def _bool(key: str, default: str) -> bool:
    return os.environ.get(key, default).lower() in ("1", "true", "yes")


SRU_BASE_URL: str = os.environ.get(
    "LEXML_SRU_URL",
    "https://www.lexml.gov.br/busca/SRU",
)
URN_RESOLVE_TEMPLATE: str = os.environ.get(
    "LEXML_URN_TEMPLATE",
    "https://www.lexml.gov.br/urn/{urn}",
)
REQUEST_TIMEOUT: float = float(os.environ.get("LEXML_TIMEOUT", "15.0"))
CACHE_TTL: int = int(os.environ.get("LEXML_CACHE_TTL", "300"))
CACHE_MAXSIZE: int = int(os.environ.get("LEXML_CACHE_MAXSIZE", "256"))
BACKEND_NAME: str = "lexml-mcp"
BACKEND_VERSION: str = "0.2.0"
SCHEMA_VERSION: str = "1.0"
MAX_REDIRECTS: int = int(os.environ.get("LEXML_MAX_REDIRECTS", "5"))

# ── New config values ──────────────────────────────────────────────────
LEXML_HTTP_CONNECT_TIMEOUT: float = float(os.environ.get("LEXML_HTTP_CONNECT_TIMEOUT", "5"))
LEXML_HTTP_READ_TIMEOUT: float = float(os.environ.get("LEXML_HTTP_READ_TIMEOUT", "20"))
LEXML_HTTP_MAX_RESPONSE_BYTES: int = int(os.environ.get("LEXML_HTTP_MAX_RESPONSE_BYTES", "5242880"))
LEXML_HTTP_MAX_RETRIES: int = int(os.environ.get("LEXML_HTTP_MAX_RETRIES", "2"))
LEXML_QUERY_MAX_LENGTH: int = int(os.environ.get("LEXML_QUERY_MAX_LENGTH", "4096"))
LEXML_MAXIMUM_RECORDS_LIMIT: int = int(os.environ.get("LEXML_MAXIMUM_RECORDS_LIMIT", "50"))
LEXML_DEBUG_RAW_RESPONSES: bool = _bool("LEXML_DEBUG_RAW_RESPONSES", "false")
LEXML_RAW_EXCERPT_MAX_CHARS: int = int(os.environ.get("LEXML_RAW_EXCERPT_MAX_CHARS", "1024"))
LEXML_LOG_LEVEL: str = os.environ.get("LEXML_LOG_LEVEL", "INFO")
LEXML_USER_AGENT: str = os.environ.get("LEXML_USER_AGENT", "lexml-mcp/0.2.0")