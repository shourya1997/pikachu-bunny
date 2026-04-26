from __future__ import annotations

from decimal import Decimal

from app.contracts import AuditState, AuditSummary, Finding, FindingSeverity, ResultCode, SourceType
from app.engine.models import ParsedDocument


def reconcile_epf(audit_id: str, parsed_documents: list[ParsedDocument]) -> AuditSummary:
    successful = [document for document in parsed_documents if document.result.ok]
    sources = [document.source for document in successful]
    evidence = [snippet for document in successful for snippet in document.snippets]
    facts_by_period, duplicate_findings = _facts_by_period(audit_id, successful)
    evidence_ids = _evidence_ids_by_fact(successful)
    findings: list[Finding] = []
    clean_months = 0

    if duplicate_findings:
        return AuditSummary(
            audit_id=audit_id,
            state=AuditState.NEEDS_REVIEW,
            truth_score=0,
            scoped_score_copy="Truth score checks only EPF contribution records in V1.0.",
            open_findings=len(duplicate_findings),
            evidence_ready_findings=0,
            sources=sources,
            evidence=evidence,
            findings=duplicate_findings,
        )

    for period, facts in sorted(facts_by_period.items()):
        salary = facts.get(SourceType.SALARY_SLIP, {})
        epf = facts.get(SourceType.EPF_PASSBOOK, {})
        if not salary or not epf:
            findings.append(
                Finding(
                    id=f"{audit_id}:{period}:missing_source",
                    period=period,
                    state=AuditState.PARTIAL,
                    severity=FindingSeverity.WARNING,
                    title="Missing source for EPF comparison",
                    explanation="Salary slip and EPF passbook records are both required for this month.",
                    evidence_ids=[],
                    result_code=ResultCode.NO_CONTRIBUTION_ROWS,
                )
            )
            continue

        month_findings = _compare_month(audit_id, period, salary, epf, evidence_ids)
        if month_findings:
            findings.extend(month_findings)
        else:
            clean_months += 1

    if findings:
        state = AuditState.CONFIRMED_MISMATCH if any(f.severity == FindingSeverity.HIGH for f in findings) else AuditState.PARTIAL
        truth_score = max(0, 100 - (50 * len([f for f in findings if f.severity == FindingSeverity.HIGH])))
    elif clean_months:
        state = AuditState.CLEAN
        truth_score = 100
    else:
        state = AuditState.NEEDS_REVIEW
        truth_score = 0

    return AuditSummary(
        audit_id=audit_id,
        state=state,
        truth_score=truth_score,
        scoped_score_copy="Truth score checks only EPF contribution records in V1.0.",
        clean_months=clean_months,
        open_findings=len(findings),
        evidence_ready_findings=len([finding for finding in findings if finding.evidence_ids]),
        sources=sources,
        evidence=evidence,
        findings=findings,
    )


def _facts_by_period(
    audit_id: str,
    parsed_documents: list[ParsedDocument],
) -> tuple[dict[str, dict[SourceType, dict[str, str]]], list[Finding]]:
    grouped: dict[str, dict[SourceType, dict[str, str]]] = {}
    duplicates: list[Finding] = []
    seen_sources: set[tuple[str, SourceType]] = set()
    for document in parsed_documents:
        periods = {fact.period for fact in document.facts}
        for period in periods:
            key = (period, document.source.source_type)
            if key in seen_sources:
                duplicates.append(
                    Finding(
                        id=f"{audit_id}:{period}:{document.source.source_type.value}:duplicate",
                        period=period,
                        state=AuditState.NEEDS_REVIEW,
                        severity=FindingSeverity.WARNING,
                        title="Duplicate source for period",
                        explanation=f"Multiple {document.source.source_type.value} files cover {period}.",
                        evidence_ids=[],
                        result_code=ResultCode.DUPLICATE_SOURCE,
                    )
                )
            seen_sources.add(key)

        for fact in document.facts:
            source_facts = grouped.setdefault(fact.period, {}).setdefault(document.source.source_type, {})
            source_facts[fact.fact_type] = fact.value
    return grouped, duplicates


def _evidence_ids_by_fact(parsed_documents: list[ParsedDocument]) -> dict[tuple[SourceType, str, str], str]:
    evidence_ids: dict[tuple[SourceType, str, str], str] = {}
    for document in parsed_documents:
        for period in document.source.month_range:
            for snippet in document.snippets:
                evidence_ids[(document.source.source_type, period, snippet.label)] = snippet.id
    return evidence_ids


def _compare_month(
    audit_id: str,
    period: str,
    salary: dict[str, str],
    epf: dict[str, str],
    evidence_ids: dict[tuple[SourceType, str, str], str],
) -> list[Finding]:
    findings: list[Finding] = []
    for fact_type, title in (
        ("employee_pf", "Employee PF mismatch"),
        ("employer_pf", "Employer PF mismatch"),
    ):
        salary_value = salary.get(fact_type)
        epf_value = epf.get(fact_type)
        if salary_value is None or epf_value is None:
            findings.append(
                Finding(
                    id=f"{audit_id}:{period}:{fact_type}:missing",
                    period=period,
                    state=AuditState.PARTIAL,
                    severity=FindingSeverity.WARNING,
                    title=f"Missing {fact_type} for comparison",
                    explanation="Both salary slip and EPF passbook values are required for this comparison.",
                    evidence_ids=[],
                    result_code=ResultCode.NO_CONTRIBUTION_ROWS,
                )
            )
            continue

        if Decimal(salary_value) != Decimal(epf_value):
            linked_evidence = [
                evidence_id
                for evidence_id in (
                    evidence_ids.get((SourceType.SALARY_SLIP, period, fact_type)),
                    evidence_ids.get((SourceType.EPF_PASSBOOK, period, fact_type)),
                )
                if evidence_id
            ]
            findings.append(
                Finding(
                    id=f"{audit_id}:{period}:{fact_type}",
                    period=period,
                    state=AuditState.CONFIRMED_MISMATCH,
                    severity=FindingSeverity.HIGH,
                    title=title,
                    explanation=f"Salary slip reports {salary_value} but EPF passbook reports {epf_value}.",
                    evidence_ids=linked_evidence,
                    result_code=ResultCode.INVALID_AMOUNT,
                )
            )

    if salary.get("employer_name") != epf.get("employer_name"):
        linked_employer_evidence = [
            evidence_id
            for evidence_id in (
                evidence_ids.get((SourceType.SALARY_SLIP, period, "employer_name")),
                evidence_ids.get((SourceType.EPF_PASSBOOK, period, "employer_name")),
            )
            if evidence_id
        ]
        findings.append(
            Finding(
                id=f"{audit_id}:{period}:employer_name",
                period=period,
                state=AuditState.NEEDS_REVIEW,
                severity=FindingSeverity.WARNING,
                title="Employer name needs review",
                explanation=f"Salary slip employer '{salary.get('employer_name')}' differs from EPF '{epf.get('employer_name')}'.",
                evidence_ids=linked_employer_evidence,
                result_code=ResultCode.EMPLOYER_IDENTITY_CONFLICT,
            )
        )

    return findings
