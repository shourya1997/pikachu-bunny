from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from fastapi import BackgroundTasks, FastAPI, HTTPException, Path as ApiPath, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.contracts import AuditState, AuditSummary, JobStatus, contract_metadata
from app.services.audit_service import AuditService

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DEFAULT_DATA_DIR = Path(os.environ.get("AUDITOS_DATA_DIR", "./data"))
MAX_IMPORT_TEXT_CHARS = 1_048_576
AUDIT_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
JOB_ID_PATTERN = r"^job-[a-f0-9]{32}$"


def cors_origins() -> list[str]:
    origins = [origin.strip() for origin in os.environ.get("AUDITOS_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")]
    if "*" in origins:
        raise ValueError("AUDITOS_CORS_ORIGINS must not include '*'.")
    return [origin for origin in origins if origin]


def resolve_spa_path(static_root: Path, full_path: str) -> Path | None:
    requested = (static_root / full_path).resolve()
    if requested.is_file() and requested.is_relative_to(static_root):
        return requested
    return None

app = FastAPI(
    title="AuditOS - Local EPF Audit API",
    version="0.1.1",
    description="Local-first EPF contribution audit API.",
)
app.state.audit_service = AuditService(DEFAULT_DATA_DIR / "audit.db")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local"}


@app.get("/api/contracts")
def contracts() -> dict[str, list[str]]:
    return contract_metadata()


class ImportRequest(BaseModel):
    salary_slip_text: str = Field(min_length=1, max_length=MAX_IMPORT_TEXT_CHARS)
    epf_passbook_text: str = Field(min_length=1, max_length=MAX_IMPORT_TEXT_CHARS)


def audit_service() -> AuditService:
    return app.state.audit_service


@app.post("/api/audits/{audit_id}/imports", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
def import_audit(
    audit_id: Annotated[str, ApiPath(pattern=AUDIT_ID_PATTERN)],
    request: ImportRequest,
    background_tasks: BackgroundTasks,
) -> JobStatus:
    service = audit_service()
    result = service.submit_import(
        audit_id,
        salary_slip_text=request.salary_slip_text,
        epf_passbook_text=request.epf_passbook_text,
    )
    if not result.ok:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE if result.message == "Import queue is full." else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=status_code, detail=result.message)

    job_id = result.details["job_id"]
    if service.auto_start and not service.run_inline:
        background_tasks.add_task(service.run_job, job_id)
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Import job was not created.")
    return job


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: Annotated[str, ApiPath(pattern=JOB_ID_PATTERN)]) -> JobStatus:
    job = audit_service().get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


@app.delete("/api/jobs/{job_id}", response_model=JobStatus)
def cancel_job(job_id: Annotated[str, ApiPath(pattern=JOB_ID_PATTERN)]) -> JobStatus:
    job = audit_service().cancel_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


@app.get("/api/audits/{audit_id}", response_model=AuditSummary)
def get_audit(audit_id: Annotated[str, ApiPath(pattern=AUDIT_ID_PATTERN)]) -> AuditSummary:
    audit = audit_service().get_audit(audit_id)
    if not audit and audit_id == "demo":
        return AuditSummary(
            audit_id="demo",
            state=AuditState.EMPTY,
            truth_score=0,
            scoped_score_copy="Truth score checks only EPF contribution records in V1.0.",
        )
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found.")
    return audit


if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    STATIC_ROOT = STATIC_DIR.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        requested = resolve_spa_path(STATIC_ROOT, full_path)
        if requested:
            return FileResponse(requested)
        return FileResponse(STATIC_ROOT / "index.html")
