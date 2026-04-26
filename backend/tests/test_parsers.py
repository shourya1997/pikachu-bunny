from pathlib import Path

from app.contracts import ResultCode, SourceType
from app.engine.parsers import parse_epf_passbook_text, parse_salary_slip_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_salary_slip_extracts_canonical_facts_and_masked_snippets() -> None:
    parsed = parse_salary_slip_text("salary-1", "salary_march.txt", FIXTURES.joinpath("salary_slip_march_2026.txt").read_text())

    assert parsed.result.ok is True
    assert parsed.source.source_type == SourceType.SALARY_SLIP
    assert parsed.source.month_range == ["2026-03"]
    facts = {(fact.period, fact.fact_type): fact.value for fact in parsed.facts}
    assert facts[("2026-03", "employee_pf")] == "6000.00"
    assert facts[("2026-03", "employer_pf")] == "6000.00"
    assert facts[("2026-03", "basic_wage")] == "50000.00"
    assert facts[("2026-03", "employer_name")] == "acme india"
    assert all(snippet.masked for snippet in parsed.snippets)
    assert "100200300400" not in " ".join(snippet.text for snippet in parsed.snippets)


def test_parse_epf_passbook_extracts_canonical_facts() -> None:
    parsed = parse_epf_passbook_text("epf-1", "epf_march.txt", FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text())

    assert parsed.result.ok is True
    assert parsed.source.source_type == SourceType.EPF_PASSBOOK
    facts = {(fact.period, fact.fact_type): fact.value for fact in parsed.facts}
    assert facts[("2026-03", "employee_pf")] == "6000.00"
    assert facts[("2026-03", "employer_pf")] == "5500.00"
    assert facts[("2026-03", "employer_name")] == "acme india"


def test_parse_salary_slip_fails_on_unsupported_layout() -> None:
    parsed = parse_salary_slip_text("salary-2", "unknown.txt", "random text without pf rows")

    assert parsed.result.ok is False
    assert parsed.result.code == ResultCode.UNSUPPORTED_LAYOUT


def test_parse_salary_slip_rejects_large_input() -> None:
    parsed = parse_salary_slip_text("salary-3", "huge.txt", "x" * 1_048_577)

    assert parsed.result.ok is False
    assert parsed.result.code == ResultCode.FILE_TOO_LARGE
