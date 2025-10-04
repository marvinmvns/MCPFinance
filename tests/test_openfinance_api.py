from __future__ import annotations

from fastapi.testclient import TestClient


def test_openfinance_contracts_empty(client: TestClient) -> None:
    r = client.get("/v1/openfinance/contracts?specs_dir=nonexistent_dir")
    assert r.status_code == 200
    assert r.json() == []

