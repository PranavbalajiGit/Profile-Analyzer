from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core.config import Settings
from app.main import create_app


def build_client(monkeypatch: MonkeyPatch, database_ok: bool) -> TestClient:
    monkeypatch.setattr("app.api.v1.health.check_database", lambda: database_ok)
    settings = Settings(
        _env_file=None,
        environment="test",
        log_json=False,
        log_level="WARNING",
    )
    return TestClient(create_app(settings))


def test_liveness_returns_metadata(monkeypatch: MonkeyPatch) -> None:
    with build_client(monkeypatch, database_ok=True) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["name"] == "Profile Analyzer"
    assert body["environment"] == "test"


def test_readiness_is_ok_when_database_answers(monkeypatch: MonkeyPatch) -> None:
    with build_client(monkeypatch, database_ok=True) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok"}}


def test_readiness_is_degraded_when_database_is_down(monkeypatch: MonkeyPatch) -> None:
    with build_client(monkeypatch, database_ok=False) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


def test_request_id_is_echoed_and_generated(monkeypatch: MonkeyPatch) -> None:
    with build_client(monkeypatch, database_ok=True) as client:
        generated = client.get("/api/v1/health")
        echoed = client.get("/api/v1/health", headers={"X-Request-ID": "test-request-id"})

    assert generated.headers["X-Request-ID"]
    assert echoed.headers["X-Request-ID"] == "test-request-id"


def test_unknown_route_returns_404_with_request_id(monkeypatch: MonkeyPatch) -> None:
    with build_client(monkeypatch, database_ok=True) as client:
        response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers["X-Request-ID"]
