# Contains persistence operations for mock endpoints.
from dataclasses import dataclass
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.models.endpoint import Endpoint


PATH_PARAM_PATTERN = re.compile(r"^\{([^}/]+)\}$")


@dataclass(frozen=True)
class EndpointMatch:
    endpoint: Endpoint
    path_params: dict[str, str]


def normalize_endpoint_method(method: str | None) -> str:
    if method is None:
        return ""

    return str(method).strip().upper()


def normalize_endpoint_path(path: str | None) -> str:
    normalized_path = str(path or "/").strip()
    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"
    if len(normalized_path) > 1:
        normalized_path = normalized_path.rstrip("/")

    return normalized_path


def create_endpoint(db: Session, endpoint: Endpoint):
    endpoint.method = normalize_endpoint_method(endpoint.method)
    endpoint.path = normalize_endpoint_path(endpoint.path)

    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)

    return endpoint

def get_db_endpoint(
    db: Session,
    method: str,
    path: str,
) -> Endpoint | None:
    query = select(Endpoint).where(
        Endpoint.method == normalize_endpoint_method(method),
        Endpoint.path == normalize_endpoint_path(path),
    )
    return db.scalars(query).first()


def get_db_endpoint_match(
    db: Session,
    method: str,
    path: str,
) -> EndpointMatch | None:
    endpoint = get_db_endpoint(db, method, path)
    if endpoint is not None:
        return EndpointMatch(endpoint=endpoint, path_params={})

    normalized_method = normalize_endpoint_method(method)
    normalized_path = normalize_endpoint_path(path)
    query = select(Endpoint).where(Endpoint.method == normalized_method)
    endpoints = sorted(
        db.scalars(query).all(),
        key=lambda candidate: _template_specificity(candidate.path),
        reverse=True,
    )

    for candidate in endpoints:
        path_params = match_endpoint_template(candidate.path, normalized_path)
        if path_params is not None:
            return EndpointMatch(endpoint=candidate, path_params=path_params)

    return None


def match_endpoint_template(
    template_path: str,
    request_path: str,
) -> dict[str, str] | None:
    template_segments = _path_segments(template_path)
    request_segments = _path_segments(request_path)
    if len(template_segments) != len(request_segments):
        return None

    path_params: dict[str, str] = {}
    for template_segment, request_segment in zip(template_segments, request_segments):
        param_match = PATH_PARAM_PATTERN.match(template_segment)
        if param_match is None:
            if template_segment != request_segment:
                return None
            continue

        param_name = param_match.group(1)
        path_params[param_name] = request_segment

    return path_params


def template_path_param_names(path: str) -> list[str]:
    return [
        match.group(1)
        for segment in _path_segments(path)
        if (match := PATH_PARAM_PATTERN.match(segment)) is not None
    ]


def path_last_param_name(path: str) -> str | None:
    segments = _path_segments(path)
    if not segments:
        return None

    match = PATH_PARAM_PATTERN.match(segments[-1])
    return match.group(1) if match is not None else None


def get_db_endpoints(db: Session):
    query = select(Endpoint)
    return db.scalars(query).all()


def _path_segments(path: str) -> list[str]:
    normalized_path = normalize_endpoint_path(path)
    if normalized_path == "/":
        return []

    return normalized_path.strip("/").split("/")


def _template_specificity(path: str) -> tuple[int, int]:
    segments = _path_segments(path)
    static_segments = sum(
        1 for segment in segments if PATH_PARAM_PATTERN.match(segment) is None
    )

    return static_segments, len(segments)
