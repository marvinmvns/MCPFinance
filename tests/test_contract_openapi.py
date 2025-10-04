from __future__ import annotations

from fastapi.testclient import TestClient


def test_openapi_basic(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert data["info"]["title"] == "clean-api"
    assert data["info"]["version"] == "1.0.0"
    # ensure users paths exist
    assert "/v1/users" in data["paths"]
    assert "/v1/users/{user_id}" in data["paths"]

