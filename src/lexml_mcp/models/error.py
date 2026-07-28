"""Structured error objects — never crash, always return a diagnostic dict.

Expanded with standard error codes: INVALID_INPUT, INVALID_CQL, INVALID_URN,
UPSTREAM_CHALLENGE, UPSTREAM_TIMEOUT, UPSTREAM_HTTP_ERROR, INVALID_XML,
SRU_DIAGNOSTIC, INTERNAL_ERROR.
"""

from dataclasses import dataclass, asdict
from typing import Any


# ── Legacy StructuredError (backward compat, used by connector) ──────────

@dataclass
class StructuredError:
    error: bool = True
    error_type: str = "unknown"
    error_message: str = ""
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def network(cls, message: str, url: str | None = None) -> "StructuredError":
        return cls(
            error_type="network_error",
            error_message=message,
            details={"url": url} if url else None,
        )

    @classmethod
    def timeout(cls, url: str | None = None) -> "StructuredError":
        return cls(
            error_type="timeout",
            error_message="Request timed out",
            details={"url": url} if url else None,
        )

    @classmethod
    def invalid_xml(cls, message: str, url: str | None = None) -> "StructuredError":
        return cls(
            error_type="invalid_xml",
            error_message=message,
            details={"url": url} if url else None,
        )

    @classmethod
    def http_error(cls, status_code: int, url: str | None = None) -> "StructuredError":
        return cls(
            error_type="http_error",
            error_message=f"HTTP {status_code}",
            details={"status_code": status_code, "url": url},
        )


# ── Standard error codes (new) ──────────────────────────────────────────

@dataclass
class ErrorCode:
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] | None = None
    record_position: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


# Pre-defined error code instances
INVALID_INPUT = ErrorCode("INVALID_INPUT", "Invalid input provided", retryable=False)
INVALID_CQL = ErrorCode("INVALID_CQL", "Invalid CQL query syntax", retryable=False)
INVALID_URN = ErrorCode("INVALID_URN", "Invalid URN syntax or disallowed host", retryable=False)
UPSTREAM_CHALLENGE = ErrorCode("UPSTREAM_CHALLENGE", "Upstream returned a challenge/verification page", retryable=True)
UPSTREAM_TIMEOUT = ErrorCode("UPSTREAM_TIMEOUT", "Upstream request timed out", retryable=True)
UPSTREAM_HTTP_ERROR = ErrorCode("UPSTREAM_HTTP_ERROR", "Upstream returned an HTTP error", retryable=True)
INVALID_XML = ErrorCode("INVALID_XML", "Invalid XML from upstream", retryable=False)
SRU_DIAGNOSTIC = ErrorCode("SRU_DIAGNOSTIC", "SRU diagnostic returned", retryable=False)
INTERNAL_ERROR = ErrorCode("INTERNAL_ERROR", "Internal server error", retryable=False)
INVALID_RECORD_SCHEMA = ErrorCode("INVALID_RECORD_SCHEMA", "Invalid record schema", retryable=False)
PAYLOAD_TOO_LARGE = ErrorCode("PAYLOAD_TOO_LARGE", "Request payload too large", retryable=False)
RESPONSE_TOO_LARGE = ErrorCode("RESPONSE_TOO_LARGE", "Upstream response exceeded size limit", retryable=False)
UPSTREAM_RATE_LIMITED = ErrorCode("UPSTREAM_RATE_LIMITED", "Upstream rate limited the request", retryable=True)
UNSAFE_REDIRECT = ErrorCode("UNSAFE_REDIRECT", "Redirect target not allowed", retryable=False)
EMPTY_RESPONSE = ErrorCode("EMPTY_RESPONSE", "Upstream returned an empty response", retryable=True)
UNEXPECTED_CONTENT = ErrorCode("UNEXPECTED_CONTENT", "Unexpected content from upstream", retryable=False)
RECORD_PARSE_ERROR = ErrorCode("RECORD_PARSE_ERROR", "Failed to parse a record", retryable=False)
CACHE_ERROR = ErrorCode("CACHE_ERROR", "Cache operation failed", retryable=False)


def error_code_to_dict(code: ErrorCode, details: dict | None = None, record_position: int | None = None) -> dict:
    """Convert an ErrorCode to a dict, optionally overriding details/record_position."""
    d = code.to_dict()
    if details is not None:
        d["details"] = details
    if record_position is not None:
        d["record_position"] = record_position
    return d