# MockAPI

A local HTTP API simulator built with Python and FastAPI. Define endpoints and response schemas, then call them to generate sample data without an external backend.

I started this project during my Python specialization course to explore HTTP APIs and schema-driven data generation. It is intended for local development and prototyping.

## What it does

- Register HTTP method/path combinations and reusable JSON response definitions.
- Generate schema-shaped responses with Faker, including nested objects, arrays, formats, examples, enums and domain-specific generators.
- Configure endpoints through a small server-rendered web interface or JSON APIs.
- Match literal paths and templates such as `/tickets/{ticket_id}`.
- Persist basic collection state in SQLite for GET, POST, PUT, PATCH and DELETE workflows when the relevant endpoints are registered.
- Filter and paginate mock collections; reset their stored state to generate fresh samples.

**Stack:** Python 3.13+, FastAPI, Pydantic, SQLAlchemy, SQLite, Faker, Jinja2 and vanilla JavaScript.

## Run locally

Use Python 3.13 or newer from the repository root:

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
~~~

On Windows, activate the virtual environment with `.venv\Scripts\activate` instead. Alternatively, with [uv](https://docs.astral.sh/uv/): `uv sync` and `uv run uvicorn app.main:app --reload`.

Open:

- [Web editor](http://127.0.0.1:8000/web/) — create schemas and endpoints.
- [Interactive API docs](http://127.0.0.1:8000/docs) — inspect the HTTP interface.

### Example: mock a users endpoint

~~~bash
curl -X POST http://127.0.0.1:8000/api/endpoints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Users",
    "method": "GET",
    "path": "/users",
    "schema": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string", "format": "uuid"},
          "email": {"type": "string", "format": "email"},
          "active": {"type": "boolean", "example": true}
        }
      }
    }
  }'

curl http://127.0.0.1:8000/mock/users
~~~

The second request returns a JSON array of users. Values such as UUIDs and email addresses are generated; `active` uses the configured example. Registered paths are **relative to `/mock`**, so the stored path is `/users`, not `/mock/users`.

## How it works

~~~text
Browser / HTTP client
      |
      +-- /web --> Jinja2 templates + vanilla JS
      |
      +-- /api --> registration services --> SQLAlchemy --> SQLite
      |
      +-- /mock --> method/path matching
                        |
                        +-- schema-driven Faker response
                        |
                        +-- persisted collection state (when applicable)
~~~

Repository structure:

| Directory | Responsibility |
| --- | --- |
| `app/api/` | Admin endpoints and dynamic mock HTTP requests |
| `app/services/` | Endpoint registration, response generation and collection state |
| `app/storage/` | SQLAlchemy models, sessions and repository queries |
| `app/web/` | Routes that render the browser UI |
| `app/ui/` | Jinja2 templates, CSS and lightweight JavaScript |

The default database is `app/mockapi.db` (ignored by Git). Tables are initialized on startup. There is no migration system.

### Stateful collections

A registered GET endpoint returning an array (or an object with an `items`, `tickets`, `data` or `results` array) can initialize a persistent mock collection. To use an individual-item operation, **register its method and path**, for example `DELETE /tickets/{ticket_id}`; a GET collection definition alone does not automatically enable other HTTP methods.

Initialization is tracked separately from the stored items: deleting every item leaves the collection empty. `POST /api/mock-state/reset` clears state globally or for a specific `resource_path`, so the next read generates new samples. Query parameters other than `limit` and `offset` filter on exact string values.

Response definitions use a subset of JSON Schema. The server does not validate request bodies against these definitions.

## Configuration and safety

The server has no authentication or authorization. Anyone with network access can change endpoint definitions and reset collection state. Do not expose it directly to a public network.

Copy `app/.env.example` to `app/.env` to configure it. Cross-origin browser access is disabled by default; explicitly set a trusted development origin when a frontend on another port needs it:

~~~dotenv
CORS_ORIGINS='["http://localhost:5173"]'
DB_NAME=mockapi.db
~~~

CORS controls browser requests; it is **not** an authentication or network security mechanism. Bind to loopback for local use.

## Limitations

MockAPI does not currently support request history, user accounts, complex response scenarios, database migrations or full JSON Schema validation. It is not a reverse proxy.
