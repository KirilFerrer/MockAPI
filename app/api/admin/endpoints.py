"""Admin API for creating and listing mock endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
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
async def receive_endpoint(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    try:
        endpoint = register_endpoint(db, data)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return serialize_endpoint(endpoint)


@router.get("")
def get_endpoint_list(db: Session = Depends(get_db)):
    return serialize_endpoints(list_endpoints(db))
