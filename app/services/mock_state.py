# Simulates persistent mock resources from registered endpoints.
from dataclasses import dataclass
from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.services.mock_engine import MockResponse, mock_response_for_endpoint
from app.storage.models.endpoint import Endpoint
from app.storage.repositories.endpoint import (
    EndpointMatch,
    get_db_endpoint_match,
    normalize_endpoint_path,
    path_last_param_name,
)
from app.storage.repositories.mock_resource import (
    clear_initialized_resources,
    is_resource_initialized,
    mark_resource_initialized,
)
from app.storage.repositories.mock_item import (
    create_mock_item,
    create_mock_items,
    delete_mock_item,
    delete_mock_items,
    get_mock_item,
    get_mock_items,
    update_mock_item,
)


COLLECTION_KEYS = ("items", "tickets", "data", "results")
CONTROL_QUERY_KEYS = {"limit", "offset"}
ITEM_METHODS = {"GET", "PUT", "PATCH", "DELETE"}

MockStateResult = tuple[MockResponse, int]


@dataclass(frozen=True)
class ResourceContext:
    resource_key: str
    collection_match: EndpointMatch
    item_id_field: str
    response_key: str | None
    item_id: str | None = None


@dataclass(frozen=True)
class CollectionShape:
    response_key: str | None


def stateful_mock_response(
    db: Session,
    endpoint_match: EndpointMatch,
    method: str,
    path: str,
    payload: Any = None,
    query_params: Mapping[str, str] | None = None,
) -> MockStateResult | None:
    normalized_method = method.upper()
    context = _resource_context(db, endpoint_match, normalized_method, path)
    if context is None:
        return None

    if normalized_method == "GET" and context.item_id is None:
        items = _ensure_seeded_collection(db, context)
        filtered_items = _filter_items([_copy_item(item.data) for item in items], query_params)
        return _collection_response(filtered_items, context.response_key), 200

    if normalized_method == "GET" and context.item_id is not None:
        _ensure_seeded_collection(db, context)
        item = get_mock_item(db, context.resource_key, context.item_id)
        if item is None:
            return {"error": "Mock item not found", context.item_id_field: context.item_id}, 404
        return _copy_item(item.data), 200

    if normalized_method == "POST" and context.item_id is None:
        _ensure_seeded_collection(db, context)
        item_data = _data_from_endpoint(endpoint_match.endpoint)
        item_data.update(_payload_item(payload))
        item_id = _ensure_item_id(db, context, item_data)
        item = create_mock_item(
            db,
            resource_key=context.resource_key,
            item_id=item_id,
            data=item_data,
        )
        return _copy_item(item.data), 201

    if normalized_method == "PUT" and context.item_id is not None:
        _ensure_seeded_collection(db, context)
        item_data = _data_from_endpoint(endpoint_match.endpoint) or _data_from_endpoint(
            context.collection_match.endpoint
        )
        item_data.update(_payload_item(payload))
        item_id = _ensure_item_id(db, context, item_data, preferred_item_id=context.item_id)
        item = get_mock_item(db, context.resource_key, context.item_id)
        if item is None:
            item = create_mock_item(
                db,
                resource_key=context.resource_key,
                item_id=item_id,
                data=item_data,
            )
        else:
            item = update_mock_item(db, item, item_id=item_id, data=item_data)
        return _copy_item(item.data), 200

    if normalized_method == "PATCH" and context.item_id is not None:
        _ensure_seeded_collection(db, context)
        item = get_mock_item(db, context.resource_key, context.item_id)
        if item is None:
            return {"error": "Mock item not found", context.item_id_field: context.item_id}, 404

        item_data = _copy_item(item.data)
        item_data.update(_payload_item(payload))
        item_id = _ensure_item_id(db, context, item_data, preferred_item_id=context.item_id)
        item = update_mock_item(db, item, item_id=item_id, data=item_data)
        return _copy_item(item.data), 200

    if normalized_method == "DELETE" and context.item_id is not None:
        _ensure_seeded_collection(db, context)
        item = get_mock_item(db, context.resource_key, context.item_id)
        if item is None:
            return {"error": "Mock item not found", context.item_id_field: context.item_id}, 404

        delete_mock_item(db, item)
        return {context.item_id_field: context.item_id, "deleted": True}, 200

    return None


def reset_mock_state(db: Session, resource_path: str | None = None) -> int:
    resource_key = _normalize_resource_key(resource_path) if resource_path is not None else None
    deleted = delete_mock_items(db, resource_key)
    clear_initialized_resources(db, resource_key)
    return deleted


def _resource_context(
    db: Session,
    endpoint_match: EndpointMatch,
    method: str,
    path: str,
) -> ResourceContext | None:
    normalized_path = normalize_endpoint_path(path)
    item_param_name = path_last_param_name(endpoint_match.endpoint.path)

    if method in ITEM_METHODS and item_param_name in endpoint_match.path_params:
        resource_key = _parent_path(normalized_path)
        if resource_key is None:
            return None
        return _item_context(db, resource_key, endpoint_match.path_params[item_param_name], item_param_name)

    if method == "GET":
        collection_shape = _collection_shape(endpoint_match.endpoint)
        if collection_shape is not None:
            return ResourceContext(
                resource_key=normalized_path,
                collection_match=endpoint_match,
                item_id_field=_infer_item_id_field(endpoint_match.endpoint),
                response_key=collection_shape.response_key,
            )

    if method in ITEM_METHODS:
        item_context = _exact_item_context(db, normalized_path)
        if item_context is not None:
            return item_context

    if method not in {"GET", "POST"}:
        return None

    collection_match = get_db_endpoint_match(db, "GET", normalized_path)
    if collection_match is None:
        return None

    collection_shape = _collection_shape(collection_match.endpoint)
    if collection_shape is None:
        return None

    response_key = collection_shape.response_key
    item_id_field = _infer_item_id_field(collection_match.endpoint)
    return ResourceContext(
        resource_key=normalized_path,
        collection_match=collection_match,
        item_id_field=item_id_field,
        response_key=response_key,
    )


def _item_context(
    db: Session,
    resource_key: str,
    item_id: str,
    item_param_name: str | None,
) -> ResourceContext | None:
    collection_match = get_db_endpoint_match(db, "GET", resource_key)
    if collection_match is None:
        return None

    collection_shape = _collection_shape(collection_match.endpoint)
    if collection_shape is None:
        return None

    item_id_field = _infer_item_id_field(collection_match.endpoint, item_param_name)
    return ResourceContext(
        resource_key=resource_key,
        collection_match=collection_match,
        item_id_field=item_id_field,
        response_key=collection_shape.response_key,
        item_id=str(item_id),
    )


def _exact_item_context(db: Session, path: str) -> ResourceContext | None:
    resource_key = _parent_path(path)
    if resource_key is None:
        return None

    item_id = path.rsplit("/", 1)[-1]
    return _item_context(db, resource_key, item_id, None)


def _ensure_seeded_collection(
    db: Session,
    context: ResourceContext,
):
    items = get_mock_items(db, context.resource_key)
    if items:
        # Existing databases can have items created before resource tracking existed.
        mark_resource_initialized(db, context.resource_key)
        return items

    # An initialized but empty collection must stay empty after DELETE.
    if is_resource_initialized(db, context.resource_key):
        return []

    seed_items = _collection_items_from_endpoint(context.collection_match.endpoint)
    normalized_items = _normalize_seed_items(db, context, seed_items)
    mark_resource_initialized(db, context.resource_key)
    if not normalized_items:
        return []

    return create_mock_items(
        db,
        resource_key=context.resource_key,
        items=normalized_items,
        id_field=context.item_id_field,
    )


def _collection_response(
    items: list[dict[str, Any]],
    response_key: str | None,
) -> MockResponse:
    if response_key is None:
        return items

    return {response_key: items}


def _collection_shape(endpoint: Endpoint) -> CollectionShape | None:
    response = mock_response_for_endpoint(endpoint)
    extracted = _extract_collection(response)
    if extracted is None:
        return None

    _, response_key = extracted
    return CollectionShape(response_key=response_key)


def _collection_items_from_endpoint(endpoint: Endpoint) -> list[Any]:
    response = mock_response_for_endpoint(endpoint)
    extracted = _extract_collection(response)
    if extracted is None:
        return []

    items, _ = extracted
    return items


def _extract_collection(response: MockResponse) -> tuple[list[Any], str | None] | None:
    if isinstance(response, list):
        return response, None

    if isinstance(response, dict):
        for key in COLLECTION_KEYS:
            value = response.get(key)
            if isinstance(value, list):
                return value, key

    return None


def _data_from_endpoint(endpoint: Endpoint) -> dict[str, Any]:
    response = mock_response_for_endpoint(endpoint)
    collection = _extract_collection(response)
    if collection is not None:
        items, _ = collection
        first_item = next((item for item in items if isinstance(item, dict)), None)
        return _copy_item(first_item) if first_item is not None else {}

    return _copy_item(response) if isinstance(response, dict) else {}


def _normalize_seed_items(
    db: Session,
    context: ResourceContext,
    items: list[Any],
) -> list[dict[str, Any]]:
    normalized_items: list[dict[str, Any]] = []
    used_item_ids = _used_item_ids(db, context.resource_key)

    for item in items:
        item_data = _payload_item(item)
        item_id = _ensure_item_id(db, context, item_data, used_item_ids=used_item_ids)
        used_item_ids.add(item_id)
        normalized_items.append(item_data)

    return normalized_items


def _ensure_item_id(
    db: Session,
    context: ResourceContext,
    item_data: dict[str, Any],
    preferred_item_id: str | None = None,
    used_item_ids: set[str] | None = None,
) -> str:
    used_ids = used_item_ids if used_item_ids is not None else _used_item_ids(db, context.resource_key)

    if preferred_item_id is not None:
        item_id = str(preferred_item_id)
        item_data[context.item_id_field] = item_id
        return item_id

    item_id = _item_id(item_data, context.item_id_field)
    if item_id is None or item_id in used_ids:
        item_id = _next_numeric_id(used_ids)

    item_data[context.item_id_field] = item_id
    return item_id


def _infer_item_id_field(
    collection_endpoint: Endpoint,
    item_param_name: str | None = None,
) -> str:
    sample_item = _first_collection_item(collection_endpoint)
    if sample_item is not None:
        for candidate in ("id", "_id", "uuid"):
            if candidate in sample_item:
                return candidate

    return item_param_name or "id"


def _first_collection_item(endpoint: Endpoint) -> dict[str, Any] | None:
    response = mock_response_for_endpoint(endpoint)
    extracted = _extract_collection(response)
    if extracted is None:
        return None

    items, _ = extracted
    return next((item for item in items if isinstance(item, dict)), None)


def _filter_items(
    items: list[dict[str, Any]],
    query_params: Mapping[str, str] | None,
) -> list[dict[str, Any]]:
    if query_params is None:
        return items

    query = dict(query_params)
    filters = {
        key: value
        for key, value in query.items()
        if key not in CONTROL_QUERY_KEYS
    }
    filtered_items = [
        item
        for item in items
        if all(str(item.get(key)) == str(value) for key, value in filters.items())
    ]

    offset = _query_int(query.get("offset"), default=0)
    limit = _query_int(query.get("limit"), default=None)
    if limit is None:
        return filtered_items[offset:]

    return filtered_items[offset : offset + limit]


def _payload_item(payload: Any) -> dict[str, Any]:
    return dict(payload) if isinstance(payload, dict) else {}


def _copy_item(item: dict[str, Any]) -> dict[str, Any]:
    return dict(item)


def _item_id(item: dict[str, Any], item_id_field: str) -> str | None:
    for candidate in ("id", "_id", "uuid", item_id_field):
        value = item.get(candidate)
        if value is not None:
            return str(value)

    return None


def _used_item_ids(db: Session, resource_key: str) -> set[str]:
    return {item.item_id for item in get_mock_items(db, resource_key)}


def _next_numeric_id(used_ids: set[str]) -> str:
    numeric_ids = [int(item_id) for item_id in used_ids if item_id.isdigit()]
    if numeric_ids:
        return str(max(numeric_ids) + 1)

    return str(len(used_ids) + 1)


def _query_int(value: str | None, default: int | None) -> int | None:
    if value is None:
        return default

    try:
        parsed_value = int(value)
    except ValueError:
        return default

    return max(parsed_value, 0)


def _parent_path(path: str) -> str | None:
    normalized_path = normalize_endpoint_path(path)
    if normalized_path == "/":
        return None

    parent = normalized_path.rsplit("/", 1)[0]
    return parent or "/"


def _normalize_resource_key(resource_path: str) -> str:
    normalized_path = normalize_endpoint_path(resource_path)
    if normalized_path.startswith("/mock/"):
        return normalize_endpoint_path(normalized_path.removeprefix("/mock"))

    return normalized_path
