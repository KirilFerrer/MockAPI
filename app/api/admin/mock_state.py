# Expone rutas administrativas para gestionar el estado persistido de mocks.
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.services.mock_state import reset_mock_state
from app.storage.database import get_db

router = APIRouter(prefix="/api/mock-state", tags=["mock-state"])


@router.post("/reset")
async def reset_state(
    request: Request,
    db: Session = Depends(get_db),
):
    body = await _optional_json(request)
    resource_path = body.get("resource_path") if isinstance(body, dict) else None
    deleted = reset_mock_state(db, resource_path)

    return {
        "deleted": deleted,
        "resource_path": resource_path,
    }


async def _optional_json(request: Request):
    try:
        return await request.json()
    except ValueError:
        return {}
