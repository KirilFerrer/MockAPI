# Registers mock endpoints from data read by the HTTP layer.
from typing import Any

from sqlalchemy.orm import Session

from app.storage.models.endpoint import Endpoint
from app.storage.models.schema import Schema
from app.services.schema_registry import get_schema
from app.storage.repositories.endpoint import (
    create_endpoint,
    get_db_endpoints,
    normalize_endpoint_method,
    normalize_endpoint_path,
)


def schema_payload(db: Session, endpoint_data: dict[str, Any]) -> Schema:
    schema_id = endpoint_data.get("schema_id")

    if schema_id:
        try:
            schema = get_schema(db, int(schema_id))
            if schema:
                return schema
        except ValueError:
            pass

    schema_name = endpoint_data.get("schema_name") or endpoint_data.get("name") or "Schema sin nombre"
    return Schema(
        name=schema_name,
        definition=endpoint_data.get("schema", {}),
    )


def endpoint_payload(db: Session, endpoint_data: dict[str, Any]) -> Endpoint:
    return Endpoint(
        name=endpoint_data.get("name") or endpoint_data.get("description"),
        description=endpoint_data.get("description"),
        method=normalize_endpoint_method(endpoint_data.get("method")),
        path=normalize_endpoint_path(endpoint_data.get("path")),
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
    return create_endpoint(db, endpoint)


def list_endpoints(db: Session) -> list[Endpoint]:
    return get_db_endpoints(db)
