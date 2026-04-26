import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "local"}


def test_demo_audit_endpoint_has_scoped_truth_score_copy(client: TestClient) -> None:
    response = client.get("/api/audits/demo")

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "empty"
    assert "EPF contribution records" in body["scoped_score_copy"]


def test_contracts_endpoint_exposes_state_vocabularies(client: TestClient) -> None:
    response = client.get("/api/contracts")

    assert response.status_code == 200
    body = response.json()
    assert "confirmed_mismatch" in body["audit_states"]
    assert "needs_review" in body["audit_states"]
