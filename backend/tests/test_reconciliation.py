from pathlib import Path

from app.contracts import AuditState, ResultCode
from app.engine.parsers import parse_epf_passbook_text, parse_salary_slip_text
from app.engine.reconcile import reconcile_epf

FIXTURES = Path(__file__).parent / "fixtures"


def test_reconcile_epf_flags_confirmed_mismatch() -> None:
    salary = parse_salary_slip_text("salary-1", "salary_march.txt", FIXTURES.joinpath("salary_slip_march_2026.txt").read_text())
    epf = parse_epf_passbook_text("epf-1", "epf_march.txt", FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text())

    summary = reconcile_epf("audit-1", [salary, epf])

    assert summary.state == AuditState.CONFIRMED_MISMATCH
    assert summary.truth_score == 50
    assert summary.open_findings == 1
    assert summary.evidence_ready_findings == 1
    assert summary.findings[0].period == "2026-03"
    assert "Employer PF mismatch" in summary.findings[0].title
    assert summary.findings[0].result_code == ResultCode.INVALID_AMOUNT
    assert set(summary.findings[0].evidence_ids).issubset({snippet.id for snippet in summary.evidence})


def test_reconcile_epf_reports_clean_when_amounts_match() -> None:
    salary = parse_salary_slip_text("salary-1", "salary_march.txt", FIXTURES.joinpath("salary_slip_march_2026.txt").read_text())
    epf = parse_epf_passbook_text(
        "epf-1",
        "epf_march.txt",
        FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text().replace("Employer Contribution: 5,500", "Employer Contribution: 6,000"),
    )

    summary = reconcile_epf("audit-1", [salary, epf])

    assert summary.state == AuditState.CLEAN
    assert summary.truth_score == 100
    assert summary.clean_months == 1
    assert summary.open_findings == 0


def test_reconcile_epf_reports_duplicate_source_for_same_period() -> None:
    salary = parse_salary_slip_text("salary-1", "salary_march.txt", FIXTURES.joinpath("salary_slip_march_2026.txt").read_text())
    duplicate_salary = parse_salary_slip_text("salary-2", "salary_march_copy.txt", FIXTURES.joinpath("salary_slip_march_2026.txt").read_text())
    epf = parse_epf_passbook_text("epf-1", "epf_march.txt", FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text())

    summary = reconcile_epf("audit-1", [salary, duplicate_salary, epf])

    assert summary.state == AuditState.NEEDS_REVIEW
    assert summary.findings[0].result_code == ResultCode.DUPLICATE_SOURCE


def test_reconcile_epf_links_employer_name_evidence() -> None:
    salary = parse_salary_slip_text("salary-1", "salary_march.txt", FIXTURES.joinpath("salary_slip_march_2026.txt").read_text())
    epf = parse_epf_passbook_text(
        "epf-1",
        "epf_march.txt",
        FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text().replace("Acme India Private Limited", "Other Company Limited"),
    )

    summary = reconcile_epf("audit-1", [salary, epf])
    employer_finding = next(finding for finding in summary.findings if finding.result_code == ResultCode.EMPLOYER_IDENTITY_CONFLICT)

    assert set(employer_finding.evidence_ids).issubset({snippet.id for snippet in summary.evidence})
    assert employer_finding.evidence_ids
