"""Search result models for SRU responses."""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SearchRecord:
    record_position: int
    record_schema: str
    data: dict[str, Any]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SearchResult:
    query: str
    request_url: str
    content_type: str
    number_of_records: int | None = None
    next_record_position: int | None = None
    records: list[dict] = field(default_factory=list)
    diagnostics: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}