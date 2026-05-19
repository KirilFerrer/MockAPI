# Groups and registers the application's public routers.
from fastapi import APIRouter

from app.api.admin import endpoints as admin_endpoints
from app.api.admin import mock_state as admin_mock_state
from app.api.admin import schemas as admin_schemas
from app.api.mock import runtime as mock_runtime
from app.web import router as web_router

router = APIRouter()

router.include_router(web_router.router)
router.include_router(admin_endpoints.router)
router.include_router(admin_schemas.router)
router.include_router(admin_mock_state.router)
router.include_router(mock_runtime.router)
