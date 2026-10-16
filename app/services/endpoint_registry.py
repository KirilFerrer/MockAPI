"""Register mock HTTP contracts and resolve their schemas."""
from typing import Any

from sqlalchemy.orm import Session

from app.services.schema_registry import get_schema
from app.storage.models.endpoint import Endpoint
from app.storage.models.schema import Schema
from app.storage.repositories.endpoint import (
    create_endpoint,
    get_db_endpoint,
    get_db_endpoints,
    normalize_endpoint_method,
    normalize_endpoint_path,
)

SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}


def schema_payload(db: Session, endpoint_data: dict[str, Any]) -> Schema:
    schema_id = endpoint_data.get("schema_id")
    if schema_id is not None:
        if isinstance(schema_id, bool):
            raise ValueError("schema_id must be a positive integer")
        try:
            schema_id = int(schema_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("schema_id must be a positive integer") from exc
        if schema_id <= 0:
            raise ValueError("schema_id must be a positive integer")
        schema = get_schema(db, schema_id)
        if schema is None:
            raise LookupError(f"Schema {schema_id} was not found")
        return schema

    definition = endpoint_data.get("schema")
    if not isinstance(definition, dict):
        raise ValueError("Provide a schema object or an existing schema_id")
    schema_name = endpoint_data.get("schema_name") or endpoint_data.get("name") or "Untitled schema"
    if not isinstance(schema_name, str):
        raise ValueError("schema_name must be a string")
    return Schema(name=schema_name.strip() or "Untitled schema", definition=definition)


def endpoint_payload(db: Session, endpoint_data: dict[str, Any]) -> Endpoint:
    if not isinstance(endpoint_data, dict):
        raise ValueError("Endpoint registration requires a JSON object")
    method = normalize_endpoint_method(endpoint_data.get("method"))
    path = endpoint_data.get("path")
    if method not in SUPPORTED_METHODS:
        raise ValueError("Unsupported or missing HTTP method")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Endpoint path is required")
    normalized_path = normalize_endpoint_path(path)
    name = endpoint_data.get("name") or endpoint_data.get("description") or f"{method} {normalized_path}"
    description = endpoint_data.get("description")
    if not isinstance(name, str) or (description is not None and not isinstance(description, str)):
        raise ValueError("Endpoint name and description must be strings")
    return Endpoint(
        name=name.strip(),
        description=description,
        method=method,
        path=normalized_path,
        schema=schema_payload(db, endpoint_data),
    )


def serialize_endpoint(endpoint: Endpoint) -> dict[str, Any]:
    return {
        "id": endpoint.id,
        "name": endpoint.name,
        "description": endpoint.description,
        "method": endpoint.method,
        "path": endpoint.path,
        "schema_id": endpoint.schema_id,
        "schema_name": endpoint.schema.name if endpoint.schema else None,
        "schema": endpoint.schema.definition if endpoint.schema else {},
    }


def serialize_endpoints(endpoints: list[Endpoint]) -> list[dict[str, Any]]:
    return [serialize_endpoint(endpoint) for endpoint in endpoints]


def register_endpoint(db: Session, endpoint_data: dict[str, Any]) -> Endpoint:
    endpoint = endpoint_payload(db, endpoint_data)
    # Lookup must not autoflush the unsaved endpoint's schema relationship.
    with db.no_autoflush:
        if get_db_endpoint(db, endpoint.method, endpoint.path) is not None:
            raise FileExistsError(f"{endpoint.method} {endpoint.path} is already registered")
    return create_endpoint(db, endpoint)


def list_endpoints(db: Session) -> list[Endpoint]:
    return get_db_endpoints(db)
