"""Challenge HTML detection for LexML SRU responses.

Detects when the SRU endpoint returns an HTML verification/challenge page
instead of valid XML. Heuristics: content-type sniffing, HTML doctype/title
patterns, and known challenge keywords.
"""

import re

_CHALLENGE_PATTERNS: list[re.Pattern] = [
    re.compile(r"<!DOCTYPE\s+html", re.IGNORECASE),
    re.compile(r"<html", re.IGNORECASE),
    re.compile(r"verifica[cç][aã]o\s+de\s+seguran[cç]a", re.IGNORECASE),
    re.compile(r"security\s+check", re.IGNORECASE),
    re.compile(r"captcha", re.IGNORECASE),
    re.compile(r"desafio\s+de\s+seguran[cç]a", re.IGNORECASE),
]


def is_challenge_html(content_type: str, body: str) -> bool:
    """Return True if the response looks like a challenge/verification page."""
    ct = content_type.lower()
    if "html" in ct:
        return True
    if "xml" in ct or "xml" not in ct:
        # Check body heuristics
        for pat in _CHALLENGE_PATTERNS:
            if pat.search(body):
                return True
    return False


def build_challenge_object(
    status_code: int,
    content_type: str,
    body: str,
) -> dict:
    """Build a structured challenge descriptor."""
    excerpt = body[:500]
    return {
        "is_challenge_like": True,
        "content_type": content_type,
        "raw_excerpt": excerpt,
        "status_code": status_code,
    }