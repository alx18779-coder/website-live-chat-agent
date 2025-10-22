"""Tests for the dashboard metrics endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_metrics_returns_payload(test_client: TestClient) -> None:
    response = test_client.get("/api/v1/metrics", params={"range": "24h"})
    assert response.status_code == 200

    payload = response.json()
    assert "kpis" in payload and len(payload["kpis"]) == 4
    assert "trend" in payload and len(payload["trend"]["timestamps"]) > 0
    assert payload["trend"]["series"]

    statuses = payload["status"]
    assert set(statuses.keys()) == {"milvus", "redis"}
    assert statuses["milvus"]["status"] in {"healthy", "degraded", "down", "unknown"}
    assert statuses["redis"]["status"] in {"healthy", "degraded", "down", "unknown"}


def test_get_metrics_rejects_invalid_range(test_client: TestClient) -> None:
    response = test_client.get("/api/v1/metrics", params={"range": "invalid"})
    assert response.status_code == 422

