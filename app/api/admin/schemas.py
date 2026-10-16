"""Admin API for creating and listing reusable schemas."""
from fastapi import APIRouter, Depends, HTTPException, Request
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
async def receive_schema(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    try:
        schema = register_schema(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return serialize_schema(schema)


@router.get("")
def get_schema_list(db: Session = Depends(get_db)):
    return serialize_schemas(list_schemas(db))
