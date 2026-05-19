# Builds mock responses from stored schemas.
from dataclasses import dataclass
from typing import Any

from faker import Faker

from app.services.mock_intentions import (
    IntentContext,
    generate_intention,
    infer_intention_key,
    tokens_from_text,
)


MockResponse = dict[str, Any] | list[Any] | str | int | float | bool | None
DEFAULT_ARRAY_SIZE = 3
ROOT_FIELD_NAME = "value"
MISSING = object()
fake = Faker()


@dataclass(frozen=True)
class MockGenerationContext:
    path: str = ""
    endpoint_name: str = ""
    schema_name: str = ""
    parent_fields: tuple[str, ...] = ()

    def with_field(self, field_name: str) -> "MockGenerationContext":
        if field_name == ROOT_FIELD_NAME:
            return self

        return MockGenerationContext(
            path=self.path,
            endpoint_name=self.endpoint_name,
            schema_name=self.schema_name,
            parent_fields=(*self.parent_fields, field_name),
        )

    def intent_context(self, field_name: str) -> IntentContext:
        parent_tokens = _tokens_from_values(self.parent_fields)
        path_tokens = tokens_from_text(self.path)
        schema_tokens = tokens_from_text(self.schema_name)
        endpoint_tokens = tokens_from_text(self.endpoint_name)
        return IntentContext(
            field_name=field_name,
            field_tokens=tokens_from_text(field_name),
            context_tokens=parent_tokens | path_tokens | schema_tokens | endpoint_tokens,
            path_tokens=path_tokens,
            schema_tokens=schema_tokens,
            parent_tokens=parent_tokens,
        )


def mock_response_for_endpoint(endpoint: Any) -> MockResponse:
    schema = getattr(endpoint, "schema", None)
    definition = getattr(schema, "definition", None)
    context = MockGenerationContext(
        path=str(getattr(endpoint, "path", "") or ""),
        endpoint_name=str(getattr(endpoint, "name", "") or ""),
        schema_name=str(getattr(schema, "name", "") or ""),
    )
    return mock_response_from_definition(definition, context)


def mock_response_from_definition(
    definition: Any,
    context: MockGenerationContext | None = None,
) -> MockResponse:
    active_context = context or MockGenerationContext()
    if not isinstance(definition, dict) or not definition:
        return {}

    if _looks_like_json_schema(definition):
        return _value_from_field_config(ROOT_FIELD_NAME, definition, active_context)

    return {
        field_name: _value_from_field_config(field_name, field_config, active_context)
        for field_name, field_config in definition.items()
    }


def _looks_like_json_schema(definition: dict[str, Any]) -> bool:
    return isinstance(definition.get("type"), str) or "properties" in definition or "items" in definition


def _value_from_field_config(
    field_name: str,
    field_config: Any,
    context: MockGenerationContext,
) -> MockResponse:
    if not isinstance(field_config, dict):
        return field_config

    intent_context = context.intent_context(field_name)
    configured_value = _configured_value(field_config, intent_context)
    if configured_value is not MISSING:
        return configured_value

    field_type = str(field_config.get("type") or "string").lower()
    field_format = str(field_config.get("format") or "").lower()

    if field_type == "array":
        return _fake_array(field_name, field_config, context)

    if field_type == "object":
        return _fake_object(field_name, field_config, context)

    inferred_value = _inferred_value(intent_context)
    if inferred_value is not MISSING:
        return _coerce_value_for_type(inferred_value, field_type)

    if field_type == "integer":
        return _fake_integer(field_name, field_config)

    if field_type == "number":
        return _fake_number(field_name, field_config)

    if field_type == "boolean":
        return fake.pybool()

    return _fake_string(field_name, field_format)


def _configured_value(
    field_config: dict[str, Any],
    context: IntentContext,
) -> MockResponse | object:
    if "example" in field_config:
        return field_config["example"]

    if "default" in field_config:
        return field_config["default"]

    example_value = _example_value(field_config)
    if example_value is not MISSING:
        return example_value

    enum = field_config.get("enum")
    if isinstance(enum, list) and enum:
        return fake.random_element(elements=enum)

    mock_config = _mock_config(field_config)
    pattern = mock_config.get("pattern")
    if isinstance(pattern, str) and pattern:
        return fake.bothify(text=pattern)

    generator_value = generate_intention(_string_value(mock_config.get("generator")), fake, context)
    if generator_value is not None:
        return generator_value

    return MISSING


def _example_value(field_config: dict[str, Any]) -> MockResponse | object:
    mock_config = _mock_config(field_config)
    for examples in (field_config.get("examples"), mock_config.get("examples")):
        if isinstance(examples, list) and examples:
            return fake.random_element(elements=examples)

    return MISSING


def _inferred_value(context: IntentContext) -> MockResponse | object:
    generator_key = infer_intention_key(context)
    generated_value = generate_intention(generator_key, fake, context)
    if generated_value is None:
        return MISSING

    return generated_value


def _fake_array(
    field_name: str,
    field_config: dict[str, Any],
    context: MockGenerationContext,
) -> list[Any]:
    items_config = field_config.get("items")
    if not items_config:
        return []

    item_context = context.with_field(field_name)
    item_name = _singular_field_name(field_name)
    return [
        _value_from_field_config(item_name, items_config, item_context)
        for _ in range(_array_size(field_config))
    ]


def _fake_object(
    field_name: str,
    field_config: dict[str, Any],
    context: MockGenerationContext,
) -> dict[str, Any]:
    properties = field_config.get("properties")
    if not isinstance(properties, dict):
        return {}

    child_context = context.with_field(field_name)
    return {
        child_name: _value_from_field_config(child_name, child_config, child_context)
        for child_name, child_config in properties.items()
    }


def _fake_integer(field_name: str, field_config: dict[str, Any]) -> int:
    tokens = tokens_from_text(field_name)
    min_value, max_value = _integer_bounds(field_config)

    if _has_any(tokens, {"age", "edad"}):
        return _random_int(
            min_value=max(min_value, 18),
            max_value=min(max_value, 90),
            fallback_min=min_value,
            fallback_max=max_value,
        )

    if _has_any(tokens, {"year", "anio", "ano"}):
        return int(fake.year())

    if _has_any(tokens, {"quantity", "qty", "count", "total", "cantidad"}):
        return _random_int(
            min_value=max(min_value, 1),
            max_value=min(max_value, 50),
            fallback_min=min_value,
            fallback_max=max_value,
        )

    if _has_any(tokens, {"stock", "capacity", "progress"}):
        return _random_int(
            min_value=max(min_value, 1),
            max_value=min(max_value, 100),
            fallback_min=min_value,
            fallback_max=max_value,
        )

    return fake.random_int(min=min_value, max=max_value)


def _fake_number(field_name: str, field_config: dict[str, Any]) -> float:
    tokens = tokens_from_text(field_name)
    min_value, max_value = _number_bounds(field_config)

    if _has_any(tokens, {"price", "amount", "cost", "total", "precio", "importe", "coste"}):
        return round(fake.random_int(min=int(min_value * 100), max=int(max_value * 100)) / 100, 2)

    return round(fake.random_int(min=int(min_value * 100), max=int(max_value * 100)) / 100, 2)


def _fake_string(field_name: str, field_format: str) -> str:
    tokens = tokens_from_text(field_name)

    if field_format in {"date-time", "datetime"} or _has_any(tokens, {"created", "updated", "timestamp"}):
        return fake.date_time_between(start_date="-1y", end_date="now").isoformat()

    if field_format == "date" or _has_any(tokens, {"date", "fecha"}):
        return fake.date_this_year().isoformat()

    if field_format in {"email", "idn-email"} or _has_any(tokens, {"email", "correo"}):
        return fake.email()

    if field_format in {"uuid"} or _has_any(tokens, {"uuid"}):
        return fake.uuid4()

    if field_format in {"uri", "url"} or _has_any(tokens, {"url", "uri", "website", "web"}):
        return fake.url()

    if _has_any(tokens, {"phone", "telefono", "tel"}):
        return fake.phone_number()

    if _has_any(tokens, {"first", "firstname"}):
        return fake.first_name()

    if _has_any(tokens, {"last", "lastname", "surname", "apellido"}):
        return fake.last_name()

    if _has_any(tokens, {"id"}):
        return fake.uuid4()

    return fake.word()


def _integer_bounds(field_config: dict[str, Any]) -> tuple[int, int]:
    min_value = _int_config(field_config.get("minimum"), default=1)
    max_value = _int_config(field_config.get("maximum"), default=9999)

    exclusive_minimum = _int_config(field_config.get("exclusiveMinimum"), default=None)
    if exclusive_minimum is not None:
        min_value = max(min_value, exclusive_minimum + 1)

    exclusive_maximum = _int_config(field_config.get("exclusiveMaximum"), default=None)
    if exclusive_maximum is not None:
        max_value = min(max_value, exclusive_maximum - 1)

    if min_value > max_value:
        return 1, 9999

    return min_value, max_value


def _number_bounds(field_config: dict[str, Any]) -> tuple[float, float]:
    min_value = _float_config(field_config.get("minimum"), default=1.0)
    max_value = _float_config(field_config.get("maximum"), default=9999.0)

    exclusive_minimum = _float_config(field_config.get("exclusiveMinimum"), default=None)
    if exclusive_minimum is not None:
        min_value = max(min_value, exclusive_minimum + 0.01)

    exclusive_maximum = _float_config(field_config.get("exclusiveMaximum"), default=None)
    if exclusive_maximum is not None:
        max_value = min(max_value, exclusive_maximum - 0.01)

    if min_value > max_value:
        return 1.0, 9999.0

    return min_value, max_value


def _random_int(
    *,
    min_value: int,
    max_value: int,
    fallback_min: int,
    fallback_max: int,
) -> int:
    if min_value <= max_value:
        return fake.random_int(min=min_value, max=max_value)

    return fake.random_int(min=fallback_min, max=fallback_max)


def _coerce_value_for_type(value: Any, field_type: str) -> MockResponse:
    try:
        if field_type == "integer":
            return int(value)

        if field_type == "number":
            return float(value)

        if field_type == "boolean":
            return bool(value)

        if field_type == "string":
            return str(value)
    except (TypeError, ValueError):
        return value

    return value


def _mock_config(field_config: dict[str, Any]) -> dict[str, Any]:
    config = field_config.get("x-mock")
    return config if isinstance(config, dict) else {}


def _string_value(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _int_config(value: Any, default: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float_config(value: Any, default: float | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _tokens_from_values(values: tuple[str, ...]) -> frozenset[str]:
    tokens: set[str] = set()
    for value in values:
        tokens.update(tokens_from_text(value))

    return frozenset(tokens)


def _has_any(tokens: frozenset[str], expected: set[str]) -> bool:
    return bool(tokens & expected)


def _singular_field_name(field_name: str) -> str:
    if field_name.endswith("ies"):
        return f"{field_name[:-3]}y"

    return field_name[:-1] if field_name.endswith("s") else field_name


def _array_size(field_config: dict[str, Any]) -> int:
    mock_config = _mock_config(field_config)
    min_items = _int_config(field_config.get("minItems"), default=None)
    mock_count = _int_config(mock_config.get("count"), default=None)
    sizes = [size for size in (min_items, mock_count) if size is not None and size > 0]
    if sizes:
        return max(sizes)

    return DEFAULT_ARRAY_SIZE
