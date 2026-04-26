from __future__ import annotations

import sqlite3
from pathlib import Path

from app.contracts import AuditSummary, EvidenceSnippet

SCHEMA = """
CREATE TABLE IF NOT EXISTS audits (
    id TEXT PRIMARY KEY,
    summary_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    confidence TEXT NOT NULL,
    month_range TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_snippets (
    id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    fact_id TEXT,
    label TEXT NOT NULL,
    text TEXT NOT NULL,
    masked INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    audit_id TEXT NOT NULL,
    period TEXT,
    state TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    explanation TEXT NOT NULL,
    evidence_ids TEXT NOT NULL,
    result_code TEXT NOT NULL
);
"""


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA)


def save_audit_summary(db_path: Path, summary: AuditSummary) -> None:
    init_db(db_path)
    summary_blob = summary.model_copy(update={"evidence": []})
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO audits (id, summary_json) VALUES (?, ?)",
            (summary.audit_id, summary_blob.model_dump_json()),
        )
        connection.execute("DELETE FROM sources WHERE audit_id = ?", (summary.audit_id,))
        connection.execute("DELETE FROM evidence_snippets WHERE audit_id = ?", (summary.audit_id,))
        connection.execute("DELETE FROM findings WHERE audit_id = ?", (summary.audit_id,))

        connection.executemany(
            """
            INSERT INTO sources (id, audit_id, source_type, filename, content_hash, confidence, month_range)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    source.id,
                    summary.audit_id,
                    source.source_type.value,
                    source.filename,
                    source.content_hash,
                    source.confidence.value,
                    ",".join(source.month_range),
                )
                for source in summary.sources
            ],
        )
        connection.executemany(
            """
            INSERT INTO evidence_snippets (id, audit_id, source_id, fact_id, label, text, masked)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    snippet.id,
                    summary.audit_id,
                    snippet.source_id,
                    snippet.fact_id,
                    snippet.label,
                    snippet.text,
                    int(snippet.masked),
                )
                for snippet in summary.evidence
            ],
        )
        connection.executemany(
            """
            INSERT INTO findings (id, audit_id, period, state, severity, title, explanation, evidence_ids, result_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    finding.id,
                    summary.audit_id,
                    finding.period,
                    finding.state.value,
                    finding.severity.value,
                    finding.title,
                    finding.explanation,
                    ",".join(finding.evidence_ids),
                    finding.result_code.value,
                )
                for finding in summary.findings
            ],
        )


def load_audit_summary(db_path: Path, audit_id: str) -> AuditSummary | None:
    init_db(db_path)
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("SELECT summary_json FROM audits WHERE id = ?", (audit_id,)).fetchone()
    if row is None:
        return None
    return AuditSummary.model_validate_json(row[0])


def load_evidence_snippets(db_path: Path, audit_id: str) -> list[EvidenceSnippet]:
    init_db(db_path)
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, source_id, fact_id, label, text, masked
            FROM evidence_snippets
            WHERE audit_id = ?
            ORDER BY id
            """,
            (audit_id,),
        ).fetchall()
    return [
        EvidenceSnippet(
            id=row[0],
            source_id=row[1],
            fact_id=row[2],
            label=row[3],
            text=row[4],
            masked=bool(row[5]),
        )
        for row in rows
    ]
