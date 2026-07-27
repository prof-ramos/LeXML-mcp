"""Provenance envelope — attached to every tool response."""

import hashlib
import time
from dataclasses import dataclass, asdict

from lexml_mcp import config


@dataclass
class Provenance:
    source_urn: str | None = None
    source_url: str | None = None
    source_kind: str | None = None
    authority: str | None = None
    retrieved_at: str | None = None
    content_hash: str | None = None
    backend_name: str = config.BACKEND_NAME
    backend_version: str = config.BACKEND_VERSION
    schema_version: str = config.SCHEMA_VERSION

    @classmethod
    def build(
        cls,
        url: str,
        body: str | None = None,
        source_kind: str = "sru",
        authority: str = "lexml.gov.br",
    ) -> "Provenance":
        h = hashlib.sha256((body or "").encode()).hexdigest()[:16]
        return cls(
            source_url=url,
            source_kind=source_kind,
            authority=authority,
            retrieved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            content_hash=h,
        )

    def to_dict(self) -> dict:
        return asdict(self)