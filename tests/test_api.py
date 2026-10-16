"""Regression tests for the public API and local web interface."""
import importlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.storage.models  # Register ORM tables with SQLAlchemy metadata.
from app.storage.database import Base, get_db

main = importlib.import_module("app.main")


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Use a fresh SQLite database for each test without touching the user's data."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine)

    def override_db():
        with testing_session() as db:
            yield db

    main.app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(main, "init_db", lambda: None)
    with TestClient(main.app) as http:
        yield http
    main.app.dependency_overrides.clear()
    engine.dispose()


def _register(client, method, path, schema):
    response = client.post(
        "/api/endpoints",
        json={"name": f"{method} {path}", "method": method, "path": path, "schema": schema},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_web_and_unmatched_requests(client):
    assert client.get("/web/").status_code == 200
    assert client.get("/web/create_endpoint_form").status_code == 200
    assert client.get("/static/css/app.css").status_code == 200
    assert client.get("/docs").status_code == 200
    missing = client.get("/mock/unknown")
    assert missing.status_code == 404
    assert missing.json()["path"] == "/unknown"


def test_schema_registration_and_stateless_mock(client):
    definition = {
        "type": "object",
        "properties": {
            "active": {"type": "boolean", "example": True},
            "email": {"type": "string", "format": "email"},
        },
    }
    schema = client.post("/api/schemas", json={"name": "User", "definition": definition})
    assert schema.status_code == 200
    schema_id = schema.json()["id"]
    assert client.get("/api/schemas").json()[0]["id"] == schema_id

    endpoint = client.post(
        "/api/endpoints",
        json={"name": "User", "method": "GET", "path": "users/me/", "schema_id": schema_id},
    )
    assert endpoint.status_code == 200
    assert endpoint.json()["path"] == "/users/me"
    assert endpoint.json()["schema_id"] == schema_id
    result = client.get("/mock/users/me")
    assert result.status_code == 200
    assert result.json()["active"] is True
    assert "@" in result.json()["email"]


@pytest.mark.parametrize("payload", [
    {},
    [],
    {"name": "No definition"},
    {"name": "Invalid", "definition": []},
])
def test_invalid_schema_returns_422(client, payload):
    assert client.post("/api/schemas", json=payload).status_code == 422


def test_invalid_endpoint_references_and_duplicates(client):
    endpoint = {"name": "Health", "method": "GET", "path": "/health", "schema": {"ok": {"example": True}}}
    assert client.post("/api/endpoints", json=endpoint).status_code == 200
    assert client.post("/api/endpoints", json=endpoint).status_code == 409
    assert client.get("/mock/health").json() == {"ok": True}

    assert client.post("/api/endpoints", json={**endpoint, "path": "/another", "schema_id": 999}).status_code == 404
    assert client.post("/api/endpoints", json={**endpoint, "path": "", "schema_id": 999}).status_code == 422
    assert client.post("/api/endpoints", json={**endpoint, "method": "INVALID"}).status_code == 422
    assert client.post("/api/endpoints", json=[]).status_code == 422
    assert client.post("/api/endpoints", data="not-json", headers={"Content-Type": "application/json"}).status_code == 400


def test_collection_mutation_delete_last_item_and_reset(client):
    collection_schema = {
        "type": "array",
        "minItems": 2,
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "title": {"type": "string", "example": "Example ticket"},
            },
        },
    }
    _register(client, "GET", "/tickets", collection_schema)
    _register(client, "POST", "/tickets", {"type": "object", "properties": {"title": {"type": "string"}}})
    _register(client, "GET", "/tickets/{ticket_id}", {})
    _register(client, "DELETE", "/tickets/{ticket_id}", {})

    seeded = client.get("/mock/tickets").json()
    assert len(seeded) == 2
    assert len({str(item["id"]) for item in seeded}) == 2
    assert len(client.get("/mock/tickets?limit=1").json()) == 1
    assert len(client.get("/mock/tickets?title=Example%20ticket").json()) == 2

    for item in seeded:
        assert client.delete(f"/mock/tickets/{item['id']}").status_code == 200
    assert client.get("/mock/tickets").json() == []
    assert client.get(f"/mock/tickets/{seeded[0]['id']}").status_code == 404

    added = client.post("/mock/tickets", json={"title": "Created ticket"})
    assert added.status_code == 201
    assert added.json()["title"] == "Created ticket"
    assert len(client.get("/mock/tickets").json()) == 1

    reset = client.post("/api/mock-state/reset", json={"resource_path": "/mock/tickets"})
    assert reset.status_code == 200
    assert reset.json()["deleted"] == 1
    assert len(client.get("/mock/tickets").json()) == 2
