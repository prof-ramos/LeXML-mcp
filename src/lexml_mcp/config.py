"""Centralized configuration for LexML MCP."""

import os

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