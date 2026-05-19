# Exposes admin routes for registering and listing reusable schemas.
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.services.schema_registry import (
    list_schemas,
    register_schema,
    serialize_schema,
    serialize_schemas,
)
from app.storage.database import get_db

router = APIRouter(prefix="/api/schemas", tags=["schema"])


@router.post("")
async def receive_schema(
    request: Request,
    db: Session = Depends(get_db),
):
    schema_data = await request.json()
    saved_schema = register_schema(db, schema_data)

    return serialize_schema(saved_schema)


@router.get("")
async def get_schema_list(
    request: Request,
    db: Session = Depends(get_db),
):
    schemas = list_schemas(db)
    return serialize_schemas(schemas)
