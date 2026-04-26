from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.audit_service import AuditService

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    app.state.audit_service = AuditService(tmp_path / "audit.db", run_inline=True)
    return TestClient(app)


def test_import_endpoint_creates_job_and_audit_summary(client: TestClient) -> None:
    response = client.post(
        "/api/audits/audit-1/imports",
        json={
            "salary_slip_text": FIXTURES.joinpath("salary_slip_march_2026.txt").read_text(),
            "epf_passbook_text": FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text(),
        },
    )

    assert response.status_code == 202
    job = response.json()
    assert job["state"] == "completed"

    audit = client.get("/api/audits/audit-1")

    assert audit.status_code == 200
    body = audit.json()
    assert body["state"] == "confirmed_mismatch"
    assert body["findings"][0]["evidence_ids"]
    assert "100200300400" not in str(body["evidence"])


def test_import_endpoint_rejects_second_active_job(tmp_path: Path) -> None:
    service = AuditService(tmp_path / "audit.db", run_inline=False)
    first = service.submit_import(
        "audit-1",
        salary_slip_text=FIXTURES.joinpath("salary_slip_march_2026.txt").read_text(),
        epf_passbook_text=FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text(),
    )
    second = service.submit_import(
        "audit-1",
        salary_slip_text=FIXTURES.joinpath("salary_slip_march_2026.txt").read_text(),
        epf_passbook_text=FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text(),
    )

    assert first.ok is True
    assert second.ok is False
    assert second.message == "Audit already has an active job."


def test_cancel_queued_job(client: TestClient, tmp_path: Path) -> None:
    app.state.audit_service = AuditService(tmp_path / "audit.db", run_inline=False, auto_start=False)
    response = client.post(
        "/api/audits/audit-2/imports",
        json={
            "salary_slip_text": FIXTURES.joinpath("salary_slip_march_2026.txt").read_text(),
            "epf_passbook_text": FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text(),
        },
    )
    job_id = response.json()["job_id"]

    cancelled = client.delete(f"/api/jobs/{job_id}")

    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"
