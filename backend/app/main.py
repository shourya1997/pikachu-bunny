from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.auth import get_current_user
from app.contracts import AuditState, AuditSummary, JobStatus, contract_metadata
from app.pocketbase_client import PocketBaseClient
from app.upload_service import UploadService

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.on_event("startup")
async def startup_sweep():
    try:
        async with PocketBaseClient() as pb:
            jobs = await pb.list("jobs", user_id="*", filter_extra="(status='running')")
            for job in jobs:
                await pb.update("jobs", job["id"], {"status": "interrupted"}, job["user_id"])
    except Exception as e:
        print(f"Startup sweep skipped: {e}")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "v1-multi-user"}


@app.get("/api/contracts")
def contracts() -> dict[str, list[str]]:
    return contract_metadata()


class ImportRequest(BaseModel):
    salary_slip_text: str
    epf_passbook_text: str


@app.post("/api/audits/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
) -> dict:
    content = await file.read()

    async with UploadService() as svc:
        audit = await svc.process_pdf(content, user_id, file.filename or "upload.pdf")

    return audit


@app.post("/api/audits/{audit_id}/imports", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def import_audit(
    audit_id: str,
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
) -> JobStatus:
    job_id = f"job-{uuid.uuid4().hex}"

    async with PocketBaseClient() as pb:
        job = await pb.create(
            "jobs",
            {
                "job_id": job_id,
                "audit_id": audit_id,
                "status": "pending",
                "result": None,
            },
            user_id,
        )

    background_tasks.add_task(process_import, audit_id, job_id, request.salary_slip_text, request.epf_passbook_text, user_id)

    return JobStatus(
        job_id=job_id,
        status="pending",
        result=None,
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user),
) -> JobStatus:
    async with PocketBaseClient() as pb:
        job = await pb.get("jobs", job_id, user_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        result=job.get("result"),
    )


@app.delete("/api/jobs/{job_id}", response_model=JobStatus)
async def cancel_job(
    job_id: str,
    user_id: str = Depends(get_current_user),
) -> JobStatus:
    async with PocketBaseClient() as pb:
        job = await pb.update("jobs", job_id, {"status": "cancelled"}, user_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        result=job.get("result"),
    )


@app.get("/api/audits/{audit_id}", response_model=AuditSummary)
async def get_audit(
    audit_id: str,
    user_id: str = Depends(get_current_user),
) -> AuditSummary:
    async with PocketBaseClient() as pb:
        audit = await pb.get("audits", audit_id, user_id)

    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found.")

    return AuditSummary(
        audit_id=audit["audit_id"],
        state=AuditState.EMPTY,
        truth_score=0,
        scoped_score_copy="Truth score checks only EPF contribution records in V1.0.",
    )


async def process_import(audit_id: str, job_id: str, salary_slip_text: str, epf_passbook_text: str, user_id: str) -> None:
    async with PocketBaseClient() as pb:
        await pb.update("jobs", job_id, {"status": "processing"}, user_id)
        try:
            result = {"status": "completed"}
            await pb.update("jobs", job_id, {"status": "completed", "result": result}, user_id)
        except Exception as e:
            await pb.update("jobs", job_id, {"status": "failed", "result": {"error": str(e)}}, user_id)


if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    STATIC_ROOT = STATIC_DIR.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        requested = resolve_spa_path(STATIC_ROOT, full_path)
        if requested:
            return FileResponse(requested)
        return FileResponse(STATIC_ROOT / "index.html")
