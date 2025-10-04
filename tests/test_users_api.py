from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import create_jwt


def _auth_headers() -> dict[str, str]:
    settings = get_settings()
    token = create_jwt("tester", ["users:write"], settings)
    return {"Authorization": f"Bearer {token}"}


def test_users_crud_and_pagination(client: TestClient) -> None:
    # empty list
    r = client.get("/v1/users")
    assert r.status_code == 200
    assert r.headers.get("ETag")
    body = r.json()
    assert body["items"] == [] and body["total"] == 0

    # create
    r = client.post("/v1/users", json={"email": "a@example.com", "full_name": "A"}, headers=_auth_headers())
    assert r.status_code == 200
    user = r.json()
    uid = user["id"]

    # idempotency
    idem_headers = {**_auth_headers(), "Idempotency-Key": "key-1"}
    r1 = client.post("/v1/users", json={"email": "b@example.com", "full_name": "B"}, headers=idem_headers)
    r2 = client.post("/v1/users", json={"email": "b@example.com", "full_name": "B"}, headers=idem_headers)
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()

    # get
    r = client.get(f"/v1/users/{uid}")
    assert r.status_code == 200

    # update
    r = client.put(f"/v1/users/{uid}", json={"email": "a2@example.com", "full_name": "AA"}, headers=_auth_headers())
    assert r.status_code == 200
    assert r.json()["email"] == "a2@example.com"

    # list with pagination
    r = client.get("/v1/users?limit=1&offset=1")
    assert r.status_code == 200
    p = r.json()
    assert p["total"] >= 2
    assert len(p["items"]) == 1

    # delete
    r = client.delete(f"/v1/users/{uid}", headers=_auth_headers())
    assert r.status_code == 204

