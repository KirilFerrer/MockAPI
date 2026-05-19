# Gestiona schemas mock a partir de datos leidos por la capa HTTP.
from typing import Any

from sqlalchemy.orm import Session

from app.storage.models.schema import Schema
from app.storage.repositories.schema import create_schema, get_db_schema, get_db_schemas


def schema_payload(schema_data: dict[str, Any]) -> Schema:
    return Schema(
        name=schema_data.get("name") or "Schema sin nombre",
        definition=schema_data.get("definition") or schema_data.get("schema") or {},
    )


def serialize_schema(schema: Schema) -> dict[str, Any]:
    return {
        "id": schema.id,
        "name": schema.name,
        "definition": schema.definition,
        "created_at": schema.created_at.isoformat() if schema.created_at else None,
    }


def serialize_schemas(schemas: list[Schema]) -> list[dict[str, Any]]:
    return [serialize_schema(schema) for schema in schemas]


def register_schema(db: Session, schema_data: dict[str, Any]) -> Schema:
    schema = schema_payload(schema_data)
    return create_schema(db, schema)


def list_schemas(db: Session) -> list[Schema]:
    return get_db_schemas(db)


def get_schema(db: Session, schema_id: int) -> Schema | None:
    return get_db_schema(db, schema_id)
