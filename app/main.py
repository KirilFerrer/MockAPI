# Creates the FastAPI application, initializes resources, and registers routers.
from contextlib import asynccontextmanager

from app.routing import router as app_routing
from app.core.settings import Settings
from app.storage.database import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)
if settings.cors_origins:
    # Only explicitly trusted frontend origins can call the unauthenticated local API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.mount(
    "/static",
    StaticFiles(directory=settings.static_dir),
    name="static",
)
app.include_router(app_routing)

@app.get("/")
def web_redirect():
    return RedirectResponse(url="/web", status_code=302)
