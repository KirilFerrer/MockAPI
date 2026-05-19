# Agrupa y registra los routers publicos de la aplicacion.
from fastapi import APIRouter

from app.api.admin import endpoints as admin_endpoints
from app.api.admin import schemas as admin_schemas
from app.web import router as web_router

router = APIRouter()

router.include_router(web_router.router)
router.include_router(admin_endpoints.router)
router.include_router(admin_schemas.router)
