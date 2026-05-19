# Expone rutas administrativas para registrar y gestionar endpoints mock.
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.services.endpoint_registry import (
    list_endpoints,
    register_endpoint,
    serialize_endpoint,
    serialize_endpoints,
)

from app.storage.database import get_db

router = APIRouter(prefix="/api/endpoints", tags=["endpoint"])


@router.post("")
async def receive_endpoint(
    request: Request,
    db: Session = Depends(get_db),
):
    endpoint_data = await request.json()
    saved_endpoint = register_endpoint(db, endpoint_data)

    return serialize_endpoint(saved_endpoint)

@router.get("")
async def get_endpoint_list(
    request: Request,
    db: Session = Depends(get_db)
):
    endpoints = list_endpoints(db)
    return serialize_endpoints(endpoints)
