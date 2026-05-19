from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services.mock_engine import mock_response_for_endpoint
from app.services.mock_state import stateful_mock_response
from app.storage.database import get_db
from app.storage.repositories.endpoint import get_db_endpoint_match

router = APIRouter(prefix="/mock", tags=["mock-runtime"])

MOCK_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


def normalize_path(path: str) -> str:
    return f"/{path}".rstrip("/") or "/"


async def request_payload(request: Request):
    if request.method not in {"POST", "PUT", "PATCH"}:
        return None

    try:
        return await request.json()
    except ValueError:
        return None


@router.api_route("", methods=MOCK_METHODS)
@router.api_route("/{path:path}", methods=MOCK_METHODS)
async def receive_dynamic_request(
    request: Request,
    path: str = "",
    db: Session = Depends(get_db),
):
    requested_path = normalize_path(path)
    payload = await request_payload(request)
    endpoint_match = get_db_endpoint_match(
        db,
        request.method,
        requested_path,
    )

    if endpoint_match is None:
        return JSONResponse(
            {
                "error": "No mock endpoint matched this request",
                "method": request.method,
                "path": requested_path,
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    stateful_response = stateful_mock_response(
        db,
        endpoint_match,
        request.method,
        requested_path,
        payload,
        request.query_params,
    )
    if stateful_response is not None:
        response_body, status_code = stateful_response
        return JSONResponse(response_body, status_code=status_code)

    return JSONResponse(
        mock_response_for_endpoint(endpoint_match.endpoint),
        status_code=status.HTTP_200_OK,
    )
