"""Standard response envelope — every tool returns this shape."""

from dataclasses import dataclass, field, asdict
from typing import Any

from lexml_mcp import config


@dataclass
class ResponseEnvelope:
    success: bool
    partial_success: bool = False
    schema_version: str = config.SCHEMA_VERSION
    operation: str = ""
    data: dict[str, Any] | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    provenance: dict[str, Any] | None = None
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = {"success": self.success, "partial_success": self.partial_success}
        for k, v in asdict(self).items():
            if k in ("success", "partial_success"):
                continue
            if v is not None or k == "data":
                base[k] = v
        return base


_ERROR_TYPE_MAP = {
    "network_error": "UPSTREAM_HTTP_ERROR",
    "timeout": "UPSTREAM_TIMEOUT",
    "invalid_xml": "INVALID_XML",
    "http_error": "UPSTREAM_HTTP_ERROR",
}


def _map_error_type(error_type: str) -> str:
    return _ERROR_TYPE_MAP.get(error_type, "INTERNAL_ERROR")


def make_envelope(result: dict[str, Any], operation: str) -> dict[str, Any]:
    """Wrap a raw result dict into the standard response envelope.

    Does not mutate the input dict.
    """
    provenance = result.get("provenance")
    diagnostics = result.get("diagnostics", [])
    cache_status = result.get("cache_status")

    errors: list[dict[str, Any]] = []
    success = True
    data: dict[str, Any] | None = None

    if result.get("error"):
        error_type = result.get("error_type", "unknown")
        error_msg = result.get("error_message", "")
        errors.append({
            "code": _map_error_type(error_type),
            "message": error_msg,
            "retryable": error_type in ("timeout", "network_error"),
            "details": result.get("details"),
            "record_position": None,
        })
        success = False
    elif result.get("is_challenge_like"):
        errors.append({
            "code": "UPSTREAM_CHALLENGE",
            "message": "Upstream returned a challenge/verification page",
            "retryable": True,
            "details": {"status_code": result.get("status_code")},
            "record_position": None,
        })
        success = False
    else:
        # Copy all non-metadata fields into data
        skip = {"provenance", "diagnostics", "cache_status", "error", "error_type",
                "error_message", "details", "is_challenge_like", "status_code",
                "raw_excerpt", "content_type"}
        data = {k: v for k, v in result.items() if k not in skip}

    partial_success = bool(diagnostics) if success else False

    env = ResponseEnvelope(
        success=success,
        partial_success=partial_success,
        operation=operation,
        data=data,
        errors=errors,
        provenance=provenance,
        diagnostics=diagnostics,
    )
    out = env.to_dict()
    if cache_status:
        out["cache_status"] = cache_status
    return out