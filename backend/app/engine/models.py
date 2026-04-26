from __future__ import annotations

from dataclasses import dataclass

from app.contracts import CanonicalFact, EvidenceSnippet, Result, SourceMetadata


@dataclass(frozen=True)
class ParsedDocument:
    result: Result
    source: SourceMetadata
    facts: list[CanonicalFact]
    snippets: list[EvidenceSnippet]
