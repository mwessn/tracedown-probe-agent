"""Tests for health and challenge-response endpoints."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from main import create_app


def test_health_returns_ok(client: TestClient) -> None:
    """GET /health returns status and version."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"


def test_challenge_success() -> None:
    """POST /health/challenge runs a Lace script and returns the token."""
    app = create_app()
    tc = TestClient(app)

    with patch("services.executor._run_health_sync", return_value="abc123") as mock:
        resp = tc.post("/health/challenge", json={
            "challenge_id": "ch-001",
            "token_url": "https://scheduler.internal/internal/health/token/ch-001",
        })

    assert resp.status_code == 200
    body = resp.json()
    assert body["challenge_id"] == "ch-001"
    assert body["token"] == "abc123"
    assert body["success"] is True
    assert body["error"] is None
    assert body["elapsed_ms"] >= 0
    mock.assert_called_once_with("https://scheduler.internal/internal/health/token/ch-001")


def test_challenge_failure() -> None:
    """POST /health/challenge reports failure when the executor errors."""
    app = create_app()
    tc = TestClient(app)

    with patch("services.executor._run_health_sync", side_effect=RuntimeError("health script failed: Connection refused")):
        resp = tc.post("/health/challenge", json={
            "challenge_id": "ch-002",
            "token_url": "https://scheduler.internal/internal/health/token/ch-002",
        })

    assert resp.status_code == 200
    body = resp.json()
    assert body["challenge_id"] == "ch-002"
    assert body["token"] is None
    assert body["success"] is False
    assert "Connection refused" in body["error"]
