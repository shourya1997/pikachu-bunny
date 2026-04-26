from __future__ import annotations

from pathlib import Path
from threading import RLock
from uuid import uuid4

from app.contracts import AuditSummary, JobState, JobStatus, Result, ResultCode
from app.engine.parsers import parse_epf_passbook_text, parse_salary_slip_text
from app.engine.reconcile import reconcile_epf
from app.engine.storage import load_audit_summary, load_evidence_snippets, save_audit_summary


class AuditService:
    """Single-process audit job coordinator for the local-only app."""

    def __init__(self, db_path: Path, max_queue: int = 8, run_inline: bool = False, auto_start: bool = True) -> None:
        self.db_path = db_path
        self.max_queue = max_queue
        self.run_inline = run_inline
        self.auto_start = auto_start
        self.jobs: dict[str, JobStatus] = {}
        self.pending_imports: dict[str, tuple[str, str, str]] = {}
        self.active_by_audit: dict[str, str] = {}
        self._lock = RLock()

    def submit_import(self, audit_id: str, *, salary_slip_text: str, epf_passbook_text: str) -> Result:
        with self._lock:
            active_job_id = self.active_by_audit.get(audit_id)
            if active_job_id and self.jobs[active_job_id].state in {JobState.QUEUED, JobState.RUNNING}:
                return Result.failure(ResultCode.DUPLICATE_SOURCE, "Audit already has an active job.")

            queued = sum(1 for job in self.jobs.values() if job.state in {JobState.QUEUED, JobState.RUNNING})
            if queued >= self.max_queue:
                return Result.failure(ResultCode.INTERNAL_ERROR, "Import queue is full.")

            job_id = f"job-{uuid4().hex}"
            self.jobs[job_id] = JobStatus(job_id=job_id, audit_id=audit_id, state=JobState.QUEUED, progress=0)
            self.pending_imports[job_id] = (audit_id, salary_slip_text, epf_passbook_text)
            self.active_by_audit[audit_id] = job_id

        if self.run_inline:
            self.run_job(job_id)

        return Result.success("import accepted", job_id=job_id)

    def run_job(self, job_id: str) -> None:
        with self._lock:
            job = self.jobs.get(job_id)
            payload = self.pending_imports.pop(job_id, None)
            if not job or not payload or job.state == JobState.CANCELLED:
                return
            self.jobs[job_id] = job.model_copy(update={"state": JobState.RUNNING, "progress": 10})
        audit_id, salary_slip_text, epf_passbook_text = payload
        try:
            salary = parse_salary_slip_text(f"{audit_id}:salary", "salary-slip.txt", salary_slip_text)
            epf = parse_epf_passbook_text(f"{audit_id}:epf", "epf-passbook.txt", epf_passbook_text)
            if not salary.result.ok:
                raise ValueError(salary.result.message)
            if not epf.result.ok:
                raise ValueError(epf.result.message)

            summary = reconcile_epf(audit_id, [salary, epf])
            with self._lock:
                if self.jobs[job_id].state == JobState.CANCELLED:
                    return
                save_audit_summary(self.db_path, summary)
                self.jobs[job_id] = JobStatus(
                    job_id=job_id,
                    audit_id=audit_id,
                    state=JobState.COMPLETED,
                    progress=100,
                    result=Result.success("audit import completed"),
                )
        except ValueError as exc:
            with self._lock:
                if self.jobs[job_id].state != JobState.CANCELLED:
                    self.jobs[job_id] = JobStatus(
                        job_id=job_id,
                        audit_id=audit_id,
                        state=JobState.FAILED,
                        progress=100,
                        result=Result.failure(ResultCode.UNSUPPORTED_LAYOUT, str(exc)),
                    )
        except Exception as exc:  # pragma: no cover - defensive last resort
            with self._lock:
                if self.jobs[job_id].state != JobState.CANCELLED:
                    self.jobs[job_id] = JobStatus(
                        job_id=job_id,
                        audit_id=audit_id,
                        state=JobState.FAILED,
                        progress=100,
                        result=Result.failure(ResultCode.INTERNAL_ERROR, "Audit import failed.", error=type(exc).__name__),
                    )
        finally:
            del salary_slip_text, epf_passbook_text, payload
            with self._lock:
                if self.active_by_audit.get(audit_id) == job_id:
                    self.active_by_audit.pop(audit_id, None)

    def get_job(self, job_id: str) -> JobStatus | None:
        with self._lock:
            return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> JobStatus | None:
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            if job.state in {JobState.QUEUED, JobState.RUNNING}:
                cancelled = job.model_copy(
                    update={
                        "state": JobState.CANCELLED,
                        "result": Result.failure(ResultCode.CANCELLED, "Job cancelled."),
                    }
                )
                self.jobs[job_id] = cancelled
                self.pending_imports.pop(job_id, None)
                if self.active_by_audit.get(job.audit_id) == job_id:
                    self.active_by_audit.pop(job.audit_id, None)
                return cancelled
            return job

    def get_audit(self, audit_id: str) -> AuditSummary | None:
        summary = load_audit_summary(self.db_path, audit_id)
        if not summary:
            return None
        return summary.model_copy(update={"evidence": load_evidence_snippets(self.db_path, audit_id)})
