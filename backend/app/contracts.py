from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    SALARY_SLIP = "salary_slip"
    EPF_PASSBOOK = "epf_passbook"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AuditState(StrEnum):
    EMPTY = "empty"
    PROCESSING = "processing"
    PARTIAL = "partial"
    CLEAN = "clean"
    CONFIRMED_MISMATCH = "confirmed_mismatch"
    NEEDS_REVIEW = "needs_review"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"


class ResultCode(StrEnum):
    OK = "ok"
    MISSING_FILE = "missing_file"
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    UNSUPPORTED_LAYOUT = "unsupported_layout"
    FILE_TOO_LARGE = "file_too_large"
    OCR_ONLY_UNSUPPORTED = "ocr_only_unsupported"
    NO_CONTRIBUTION_ROWS = "no_contribution_rows"
    INVALID_PERIOD = "invalid_period"
    INVALID_AMOUNT = "invalid_amount"
    DUPLICATE_SOURCE = "duplicate_source"
    EMPLOYER_IDENTITY_CONFLICT = "employer_identity_conflict"
    REDACTION_REQUIRED = "redaction_required"
    STORAGE_WRITE_FAILED = "storage_write_failed"
    STORAGE_CORRUPT = "storage_corrupt"
    CANCELLED = "cancelled"
    INTERNAL_ERROR = "internal_error"


class Result(BaseModel):
    ok: bool
    code: ResultCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def success(cls, message: str = "ok", **details: Any) -> "Result":
        return cls(ok=True, code=ResultCode.OK, message=message, details=details)

    @classmethod
    def failure(cls, code: ResultCode, message: str, **details: Any) -> "Result":
        return cls(ok=False, code=code, message=message, details=details)


class SourceMetadata(BaseModel):
    id: str
    source_type: SourceType
    filename: str
    content_hash: str
    confidence: Confidence
    month_range: list[str] = Field(default_factory=list)


class CanonicalFact(BaseModel):
    id: str
    source_id: str
    period: str = Field(pattern=r"^\d{4}-\d{2}$")
    fact_type: Literal["employee_pf", "employer_pf", "employer_name", "basic_wage"]
    value: str
    confidence: Confidence


class EvidenceSnippet(BaseModel):
    id: str
    source_id: str
    fact_id: str | None = None
    label: str
    text: str
    masked: bool = True


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"


class Finding(BaseModel):
    id: str
    period: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    state: AuditState
    severity: FindingSeverity
    title: str
    explanation: str
    evidence_ids: list[str] = Field(default_factory=list)
    result_code: ResultCode = ResultCode.OK


class AuditSummary(BaseModel):
    audit_id: str
    state: AuditState
    truth_score: int = Field(ge=0, le=100)
    scoped_score_copy: str
    clean_months: int = 0
    open_findings: int = 0
    evidence_ready_findings: int = 0
    sources: list[SourceMetadata] = Field(default_factory=list)
    evidence: list[EvidenceSnippet] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)


class JobStatus(BaseModel):
    job_id: str
    audit_id: str
    state: JobState
    progress: int = Field(ge=0, le=100)
    result: Result | None = None


def contract_metadata() -> dict[str, list[str]]:
    return {
        "audit_states": [state.value for state in AuditState],
        "job_states": [state.value for state in JobState],
        "result_codes": [code.value for code in ResultCode],
        "source_types": [source.value for source in SourceType],
    }
