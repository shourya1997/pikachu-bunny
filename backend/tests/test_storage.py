from pathlib import Path

from app.engine.parsers import parse_epf_passbook_text, parse_salary_slip_text
from app.engine.reconcile import reconcile_epf
from app.engine.storage import init_db, load_audit_summary, load_evidence_snippets, save_audit_summary

FIXTURES = Path(__file__).parent / "fixtures"


def test_storage_round_trip_keeps_masked_evidence(tmp_path: Path) -> None:
    db_path = tmp_path / "audit.db"
    init_db(db_path)
    salary = parse_salary_slip_text("salary-1", "salary_march.txt", FIXTURES.joinpath("salary_slip_march_2026.txt").read_text())
    epf = parse_epf_passbook_text("epf-1", "epf_march.txt", FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text())
    summary = reconcile_epf("audit-1", [salary, epf])

    save_audit_summary(db_path, summary)
    loaded = load_audit_summary(db_path, "audit-1")
    snippets = load_evidence_snippets(db_path, "audit-1")

    assert loaded is not None
    assert loaded.audit_id == "audit-1"
    assert loaded.evidence == []
    assert loaded.findings[0].title == summary.findings[0].title
    assert loaded.sources[0].content_hash
    assert snippets
    assert "100200300400" not in " ".join(snippet.text for snippet in snippets)
