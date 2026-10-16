# Semantic generators for enriching mock responses without new dependencies.
import re
from dataclasses import dataclass
from typing import Any, Callable

from faker import Faker


TokenSet = frozenset[str]


@dataclass(frozen=True)
class IntentContext:
    field_tokens: TokenSet
    context_tokens: TokenSet


IntentGenerator = Callable[[Faker, IntentContext], Any]


CASE_TITLE_PARTS = [
    ("VPN access", "fails for remote employees"),
    ("Billing dashboard", "does not load for finance users"),
    ("Laptop provisioning", "is blocked by missing approval"),
    ("Customer portal", "shows stale case status"),
    ("SSO login", "returns an invalid session error"),
    ("Invoice export", "times out during month close"),
    ("Inventory sync", "is delayed after asset updates"),
    ("Purchase approval", "is waiting on budget validation"),
]

CASE_DESCRIPTIONS = [
    "Users can reproduce the issue from the main dashboard after refreshing the session.",
    "The affected team needs a temporary workaround before the next operations window.",
    "Several related requests were reported after the last configuration change.",
    "The frontend should keep showing the case while the backend workflow is reviewed.",
    "The current response is enough to unblock UI validation and acceptance testing.",
]

CASE_IMPACTS = [
    "Blocks daily operations for a small internal team",
    "Prevents invoice review before approval",
    "Delays onboarding for new employees",
    "Impacts reporting accuracy for managers",
    "Creates duplicate manual work for support agents",
]

CASE_NOTES = [
    "Initial triage completed and owner assigned.",
    "Waiting for confirmation from the requesting team.",
    "Temporary workaround shared with affected users.",
    "Needs validation after the next deployment.",
    "Related asset and user records were reviewed.",
]

OPS_QUEUES = [
    "Service Desk",
    "IT Operations",
    "Finance Ops",
    "Procurement",
    "Platform Support",
    "Security Review",
]

DEPARTMENTS = [
    "Operations",
    "Finance",
    "Procurement",
    "IT Support",
    "Customer Success",
    "People Ops",
    "Security",
]

TEAMS = [
    "Platform",
    "Service Desk",
    "Billing Ops",
    "Asset Management",
    "Procurement Ops",
    "Employee Experience",
]

ROLES = [
    "operator",
    "manager",
    "finance",
    "it_admin",
    "procurement_lead",
    "support_agent",
]

VENDORS = [
    "Northwind Systems",
    "Contoso Services",
    "BluePeak Hardware",
    "Acme Cloud",
    "Fabrikam Logistics",
    "Globex Security",
]

DEVICE_NAMES = [
    "Finance laptop",
    "Support workstation",
    "Operations tablet",
    "Build server",
    "Meeting room display",
    "Warehouse scanner",
]

OPERATING_SYSTEMS = [
    "Windows 11 Pro",
    "macOS Sonoma",
    "Ubuntu 24.04 LTS",
    "iOS 18",
    "Android Enterprise",
]

WORKFLOW_STATUSES = [
    "draft",
    "submitted",
    "in_review",
    "approved",
    "blocked",
    "closed",
]

CASE_STATUSES = [
    "open",
    "in_progress",
    "waiting",
    "overdue",
    "closed",
]

ASSET_STATUSES = [
    "online",
    "offline",
    "maintenance",
    "assigned",
    "retired",
]

EMPLOYEE_STATUSES = [
    "active",
    "invited",
    "suspended",
    "offboarding",
]

INVOICE_STATUSES = [
    "received",
    "approved",
    "paid",
    "overdue",
    "disputed",
]

PURCHASE_STATUSES = [
    "draft",
    "submitted",
    "approved",
    "rejected",
    "fulfilled",
]

PRIORITIES = [
    "low",
    "normal",
    "high",
    "critical",
]

TAGS = [
    "frontend",
    "billing",
    "asset",
    "finance",
    "onboarding",
    "urgent",
    "blocked",
    "qa",
]


def tokens_from_text(value: Any) -> TokenSet:
    normalized_value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value or ""))
    return frozenset(
        token
        for token in re.split(r"[^a-zA-Z0-9]+", normalized_value.lower())
        if token
    )


def generate_intention(
    generator_key: str | None,
    fake: Faker,
    context: IntentContext,
) -> Any:
    if not generator_key:
        return None

    generator = INTENT_GENERATORS.get(generator_key)
    if generator is None:
        return None

    return generator(fake, context)


def infer_intention_key(context: IntentContext) -> str | None:
    tokens = context.field_tokens
    all_tokens = tokens | context.context_tokens

    if _has(tokens, {"impact", "afectacion"}):
        return "ops.impact"

    if _has(tokens, {"note", "notes", "comment", "comments", "nota", "notas"}):
        return "ops.note"

    if _has(tokens, {"queue", "cola"}):
        return "ops.queue"

    if _has(tokens, {"sla"}):
        return "ops.sla"

    if _has(tokens, {"priority", "prioridad"}):
        return "workflow.priority"

    if _has(tokens, {"status", "estado"}):
        return _status_intention(all_tokens)

    if _has(tokens, {"invoice"}) and _has(tokens, {"number", "num", "no"}):
        return "finance.invoice_number"

    if _has(tokens, {"purchase", "po", "order"}) and _has(tokens, {"number", "num", "no"}):
        return "finance.purchase_order"

    if _has(tokens, {"amount", "price", "cost", "total", "importe", "precio", "coste"}):
        return "finance.amount"

    if _has(tokens, {"currency", "moneda"}):
        return "finance.currency"

    if _has(tokens, {"vendor", "supplier", "provider", "customer", "client", "company", "empresa", "cliente"}):
        return "company.name"

    if _has(tokens, {"asset"}) and _has(tokens, {"tag"}):
        return "asset.tag"

    if _has(tokens, {"serial"}):
        return "asset.serial"

    if _has(tokens, {"hostname", "host"}):
        return "asset.hostname"

    if _has(tokens, {"os", "platform", "sistema"}):
        return "asset.os"

    if _has(tokens, {"department", "departamento", "area"}):
        return "person.department"

    if _has(tokens, {"team", "equipo"}):
        return "person.team"

    if _has(tokens, {"role", "rol", "position", "puesto"}):
        return "person.role"

    if _has(tokens, {"tag", "tags", "label", "labels", "etiqueta", "etiquetas"}):
        return "general.tag"

    if _has(tokens, {"title", "subject", "asunto", "titulo"}):
        if _is_case_context(all_tokens):
            return "ops.case_title"
        return "general.title"

    if _has(tokens, {"description", "desc", "body", "message", "detalle", "descripcion"}):
        if _is_case_context(all_tokens):
            return "ops.case_description"
        return "general.description"

    if _has(tokens, {"name", "nombre"}):
        if _is_asset_context(all_tokens):
            return "asset.name"
        if _has(all_tokens, {"vendor", "supplier", "provider", "customer", "client", "company", "empresa", "cliente"}):
            return "company.name"
        return "person.employee_name"

    if _has(tokens, {"owner", "assignee", "requester", "organizer", "responsable"}):
        return "person.employee_name"

    return None


def _status_intention(tokens: TokenSet) -> str:
    if _is_asset_context(tokens):
        return "asset.status"

    if _has(tokens, {"employee", "employees", "user", "users", "usuario", "empleado"}):
        return "person.status"

    if _has(tokens, {"invoice", "billing", "factura", "facturas"}):
        return "finance.invoice_status"

    if _has(tokens, {"purchase", "order", "procurement", "compra", "pedido"}):
        return "finance.purchase_status"

    if _is_case_context(tokens):
        return "ops.case_status"

    return "workflow.status"


def _case_title(fake: Faker, context: IntentContext) -> str:
    subject, detail = fake.random_element(elements=CASE_TITLE_PARTS)
    return f"{subject} {detail}"


def _case_description(fake: Faker, context: IntentContext) -> str:
    return fake.random_element(elements=CASE_DESCRIPTIONS)


def _choice(elements: list[Any]) -> IntentGenerator:
    def generator(fake: Faker, context: IntentContext) -> Any:
        return fake.random_element(elements=elements)

    return generator


def _amount(fake: Faker, context: IntentContext) -> float:
    return round(fake.random_int(min=1200, max=2500000) / 100, 2)


def _asset_tag(fake: Faker, context: IntentContext) -> str:
    return fake.bothify(text="AS-#####").upper()


def _asset_serial(fake: Faker, context: IntentContext) -> str:
    return fake.bothify(text="SN-########").upper()


def _asset_hostname(fake: Faker, context: IntentContext) -> str:
    return fake.hostname()


def _invoice_number(fake: Faker, context: IntentContext) -> str:
    return fake.bothify(text="INV-####-###").upper()


def _purchase_order(fake: Faker, context: IntentContext) -> str:
    return fake.bothify(text="PO-####-###").upper()


def _sla(fake: Faker, context: IntentContext) -> str:
    return f"{fake.random_int(min=1, max=8)}h"


def _general_title(fake: Faker, context: IntentContext) -> str:
    return fake.sentence(nb_words=4).rstrip(".")


def _general_description(fake: Faker, context: IntentContext) -> str:
    return fake.paragraph(nb_sentences=2)


def _general_tag(fake: Faker, context: IntentContext) -> str:
    return fake.random_element(elements=TAGS)


INTENT_GENERATORS: dict[str, IntentGenerator] = {
    "ops.case_title": _case_title,
    "ops.case_description": _case_description,
    "ops.impact": _choice(CASE_IMPACTS),
    "ops.note": _choice(CASE_NOTES),
    "ops.queue": _choice(OPS_QUEUES),
    "ops.sla": _sla,
    "ops.case_status": _choice(CASE_STATUSES),
    "asset.tag": _asset_tag,
    "asset.hostname": _asset_hostname,
    "asset.name": _choice(DEVICE_NAMES),
    "asset.serial": _asset_serial,
    "asset.os": _choice(OPERATING_SYSTEMS),
    "asset.status": _choice(ASSET_STATUSES),
    "finance.invoice_number": _invoice_number,
    "finance.purchase_order": _purchase_order,
    "finance.amount": _amount,
    "finance.currency": _choice(["EUR", "USD", "GBP"]),
    "finance.invoice_status": _choice(INVOICE_STATUSES),
    "finance.purchase_status": _choice(PURCHASE_STATUSES),
    "company.name": _choice(VENDORS),
    "person.employee_name": lambda fake, context: fake.name(),
    "person.department": _choice(DEPARTMENTS),
    "person.team": _choice(TEAMS),
    "person.role": _choice(ROLES),
    "person.status": _choice(EMPLOYEE_STATUSES),
    "workflow.status": _choice(WORKFLOW_STATUSES),
    "workflow.priority": _choice(PRIORITIES),
    "general.title": _general_title,
    "general.description": _general_description,
    "general.tag": _general_tag,
}


def _has(tokens: TokenSet, expected: set[str]) -> bool:
    return bool(tokens & expected)


def _is_case_context(tokens: TokenSet) -> bool:
    return _has(tokens, {"case", "cases", "ticket", "tickets", "incident", "incidents", "support"})


def _is_asset_context(tokens: TokenSet) -> bool:
    return _has(tokens, {"asset", "assets", "device", "devices", "hardware", "inventory", "activo", "activos"})
