from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.contracts import AuditState, AuditSummary
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
    assert body["evidence"]
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


def test_cancel_queued_job(tmp_path: Path) -> None:
    app.state.audit_service = AuditService(tmp_path / "audit.db", run_inline=False, auto_start=False)
    with TestClient(app) as local_client:
        response = local_client.post(
            "/api/audits/audit-2/imports",
            json={
                "salary_slip_text": FIXTURES.joinpath("salary_slip_march_2026.txt").read_text(),
                "epf_passbook_text": FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text(),
            },
        )
        job_id = response.json()["job_id"]

        cancelled = local_client.delete(f"/api/jobs/{job_id}")

    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"


def test_cancel_running_job_skips_persistence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service = AuditService(tmp_path / "audit.db", run_inline=False)
    result = service.submit_import(
        "audit-3",
        salary_slip_text=FIXTURES.joinpath("salary_slip_march_2026.txt").read_text(),
        epf_passbook_text=FIXTURES.joinpath("epf_passbook_march_2026.txt").read_text(),
    )
    job_id = result.details["job_id"]

    def cancel_during_reconcile(audit_id: str, documents: object) -> AuditSummary:
        service.cancel_job(job_id)
        return AuditSummary(
            audit_id=audit_id,
            state=AuditState.CONFIRMED_MISMATCH,
            truth_score=50,
            scoped_score_copy="Should not persist after cancellation.",
        )

    monkeypatch.setattr("app.services.audit_service.reconcile_epf", cancel_during_reconcile)

    service.run_job(job_id)

    assert service.get_job(job_id).state == "cancelled"
    assert service.get_audit("audit-3") is None


def test_import_endpoint_rejects_invalid_audit_id(client: TestClient) -> None:
    response = client.post(
        "/api/audits/bad:id/imports",
        json={
            "salary_slip_text": "x",
            "epf_passbook_text": "x",
        },
    )

    assert response.status_code == 422


def test_job_endpoint_rejects_invalid_job_id(client: TestClient) -> None:
    response = client.get("/api/jobs/not-a-job")

    assert response.status_code == 422


def test_import_endpoint_rejects_oversized_text(client: TestClient) -> None:
    response = client.post(
        "/api/audits/audit-4/imports",
        json={
            "salary_slip_text": "x" * (1_048_576 + 1),
            "epf_passbook_text": "x",
        },
    )

    assert response.status_code == 422


def test_import_endpoint_reports_queue_full(tmp_path: Path) -> None:
    app.state.audit_service = AuditService(tmp_path / "audit.db", max_queue=0, run_inline=False, auto_start=False)
    with TestClient(app) as local_client:
        response = local_client.post(
            "/api/audits/audit-5/imports",
            json={
                "salary_slip_text": "x",
                "epf_passbook_text": "x",
            },
        )

    assert response.status_code == 503
