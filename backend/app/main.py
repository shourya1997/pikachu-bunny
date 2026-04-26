from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.contracts import AuditState, AuditSummary, contract_metadata

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def resolve_spa_path(static_root: Path, full_path: str) -> Path | None:
    requested = (static_root / full_path).resolve()
    if requested.is_file() and requested.is_relative_to(static_root):
        return requested
    return None

app = FastAPI(
    title="Pikachu Bunny Audit API",
    version="0.1.0",
    description="Local-first EPF contribution audit API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "local"}


@app.get("/api/contracts")
def contracts() -> dict[str, list[str]]:
    return contract_metadata()


@app.get("/api/audits/demo", response_model=AuditSummary)
def demo_audit() -> AuditSummary:
    return AuditSummary(
        audit_id="demo",
        state=AuditState.EMPTY,
        truth_score=0,
        scoped_score_copy="Truth score checks only EPF contribution records in V1.0.",
    )


if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    STATIC_ROOT = STATIC_DIR.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        requested = resolve_spa_path(STATIC_ROOT, full_path)
        if requested:
            return FileResponse(requested)
        return FileResponse(STATIC_ROOT / "index.html")
