from __future__ import annotations

import hashlib
import re
from typing import Literal

from app.contracts import CanonicalFact, Confidence, EvidenceSnippet, Result, ResultCode, SourceMetadata, SourceType
from app.engine.models import ParsedDocument
from app.engine.normalization import normalize_amount, normalize_employer, normalize_period
from app.engine.redaction import mask_sensitive

FactType = Literal["employee_pf", "employer_pf", "employer_name", "basic_wage"]
MAX_TEXT_BYTES = 1_048_576


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _line_value(label: str, text: str) -> str | None:
    match = re.search(rf"(?im)^{re.escape(label)}:\s*(.+)$", text)
    return match.group(1).strip() if match else None


def _source(source_id: str, source_type: SourceType, filename: str, text: str, periods: list[str]) -> SourceMetadata:
    return SourceMetadata(
        id=source_id,
        source_type=source_type,
        filename=filename,
        content_hash=_content_hash(text),
        confidence=Confidence.HIGH,
        month_range=periods,
    )


def _fact(source_id: str, period: str, fact_type: FactType, value: str) -> CanonicalFact:
    return CanonicalFact(
        id=f"{source_id}:{period}:{fact_type}",
        source_id=source_id,
        period=period,
        fact_type=fact_type,
        value=value,
        confidence=Confidence.HIGH,
    )


def _snippet(source_id: str, label: str, text: str, fact_id: str | None = None) -> EvidenceSnippet:
    return EvidenceSnippet(
        id=f"{source_id}:snippet:{label}",
        source_id=source_id,
        fact_id=fact_id,
        label=label,
        text=mask_sensitive(text),
        masked=True,
    )


def _failure(
    source_id: str,
    source_type: SourceType,
    filename: str,
    text: str,
    message: str,
    code: ResultCode = ResultCode.UNSUPPORTED_LAYOUT,
) -> ParsedDocument:
    return ParsedDocument(
        result=Result.failure(code, message),
        source=_source(source_id, source_type, filename, text, []),
        facts=[],
        snippets=[_snippet(source_id, "unsupported_layout", mask_sensitive(text)[:500])],
    )


def parse_salary_slip_text(source_id: str, filename: str, text: str) -> ParsedDocument:
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        return _failure(source_id, SourceType.SALARY_SLIP, filename, "", "File is too large", ResultCode.FILE_TOO_LARGE)
    try:
        period = normalize_period(_required("Month", text))
        employee_pf = normalize_amount(_required("Employee PF", text))
        employer_pf = normalize_amount(_required("Employer PF", text))
        basic_wage = normalize_amount(_required("Basic Wage", text))
        employer = normalize_employer(_required("Employer", text))
    except ValueError as exc:
        return _failure(source_id, SourceType.SALARY_SLIP, filename, text, str(exc))

    facts = [
        _fact(source_id, period, "employee_pf", str(employee_pf)),
        _fact(source_id, period, "employer_pf", str(employer_pf)),
        _fact(source_id, period, "basic_wage", str(basic_wage)),
        _fact(source_id, period, "employer_name", employer),
    ]
    return ParsedDocument(
        result=Result.success("salary slip parsed"),
        source=_source(source_id, SourceType.SALARY_SLIP, filename, text, [period]),
        facts=facts,
        snippets=[_snippet(source_id, fact.fact_type, _evidence_line(fact.fact_type, text), fact.id) for fact in facts],
    )


def parse_epf_passbook_text(source_id: str, filename: str, text: str) -> ParsedDocument:
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        return _failure(source_id, SourceType.EPF_PASSBOOK, filename, "", "File is too large", ResultCode.FILE_TOO_LARGE)
    try:
        period = normalize_period(_required("Wage Month", text))
        employee_pf = normalize_amount(_required("Employee Contribution", text))
        employer_pf = normalize_amount(_required("Employer Contribution", text))
        employer = normalize_employer(_required("Establishment", text))
    except ValueError as exc:
        return _failure(source_id, SourceType.EPF_PASSBOOK, filename, text, str(exc))

    facts = [
        _fact(source_id, period, "employee_pf", str(employee_pf)),
        _fact(source_id, period, "employer_pf", str(employer_pf)),
        _fact(source_id, period, "employer_name", employer),
    ]
    return ParsedDocument(
        result=Result.success("epf passbook parsed"),
        source=_source(source_id, SourceType.EPF_PASSBOOK, filename, text, [period]),
        facts=facts,
        snippets=[_snippet(source_id, fact.fact_type, _evidence_line(fact.fact_type, text), fact.id) for fact in facts],
    )


def _required(label: str, text: str) -> str:
    value = _line_value(label, text)
    if value is None:
        raise ValueError(f"Missing {label}")
    return value


def _evidence_line(fact_type: FactType, text: str) -> str:
    labels = {
        "employee_pf": ("Employee PF", "Employee Contribution"),
        "employer_pf": ("Employer PF", "Employer Contribution"),
        "basic_wage": ("Basic Wage",),
        "employer_name": ("Employer", "Establishment"),
    }
    for label in labels[fact_type]:
        value = _line_value(label, text)
        if value is not None:
            return f"{label}: {value}"
    return ""
