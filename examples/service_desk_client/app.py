from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Northstar Service Desk",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

PAGES = {
    "/": "index.html",
    "/tickets/": "tickets/index.html",
    "/tickets/new.html": "tickets/new.html",
    "/tickets/detail.html": "tickets/detail.html",
    "/tickets/edit.html": "tickets/edit.html",
    "/assets/": "assets/index.html",
    "/assets/new.html": "assets/new.html",
    "/assets/detail.html": "assets/detail.html",
    "/assets/edit.html": "assets/edit.html",
    "/vendors/": "vendors/index.html",
    "/vendors/new.html": "vendors/new.html",
    "/vendors/detail.html": "vendors/detail.html",
    "/vendors/edit.html": "vendors/edit.html",
}


def html_page(filename: str):
    def response():
        return FileResponse(BASE_DIR / filename)

    return response


for url_path, filename in PAGES.items():
    app.add_api_route(url_path, html_page(filename), include_in_schema=False)
