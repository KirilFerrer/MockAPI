"""Admin API for resetting persisted mock data safely."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.services.mock_state import reset_mock_state
from app.storage.database import get_db

router = APIRouter(prefix="/api/mock-state", tags=["mock-state"])


@router.post("/reset")
async def reset_state(request: Request, db: Session = Depends(get_db)):
    if await request.body():
        try:
            body = await request.json()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON body") from exc
    else:
        body = {}

    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Expected a JSON object")

    resource_path = body.get("resource_path")
    if resource_path is not None and (
        not isinstance(resource_path, str) or not resource_path.strip()
    ):
        raise HTTPException(status_code=422, detail="resource_path must be a non-empty string")

    return {
        "deleted": reset_mock_state(db, resource_path),
        "resource_path": resource_path,
    }
