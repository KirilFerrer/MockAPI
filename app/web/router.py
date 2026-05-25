# Renders mockAPI admin HTML pages.
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.services.endpoint_registry import list_endpoints, serialize_endpoints
from app.services.schema_registry import list_schemas, serialize_schemas
from app.storage.database import get_db

router = APIRouter(prefix = "/web", tags = ["website"])
settings = Settings()

templates = Jinja2Templates(directory = settings.templates_dir)

@router.get("/")
async def homepage(request: Request, db: Session = Depends(get_db)):
    endpoints = serialize_endpoints(list_endpoints(db))
    schemas = serialize_schemas(list_schemas(db))
    return templates.TemplateResponse(
        request,
        "home.html",
        {"endpoints": endpoints, "schemas": schemas},
    )

@router.get("/endpoints")
async def endpoints_dashboard(request: Request, db: Session = Depends(get_db)):
    endpoints = serialize_endpoints(list_endpoints(db))
    return templates.TemplateResponse(
        request,
        "endpoints_dashboard.html",
        {"endpoints": endpoints},
    )

@router.get("/schemas")
async def schemas_dashboard(request: Request, db: Session = Depends(get_db)):
    schemas = serialize_schemas(list_schemas(db))
    return templates.TemplateResponse(
        request,
        "schemas_dashboard.html",
        {"schemas": schemas},
    )

@router.get("/create_endpoint_form")
def create_endpoint_form(request:Request):
    return templates.TemplateResponse(request, "create_endpoint_form.html")
