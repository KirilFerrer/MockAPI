# Northstar Service Desk: guia de contratos

Northstar es la web cliente de prueba. Gestiona tres recursos: **tickets**, **activos** y **proveedores**. La web corre en `8010` y consume los endpoints mock publicados por mockAPI en `8000`.

## Arranque

Terminal 1, mockAPI:

```bash
DB_NAME=mockapi_service_desk.db uv run uvicorn app.main:app --reload --port 8000
```

Terminal 2, web cliente:

```bash
uv run uvicorn examples.service_desk_client.app:app --reload --port 8010
```

Abrir:

```text
http://127.0.0.1:8010
```

La web apunta por defecto a:

```text
http://127.0.0.1:8000/mock
```

En mockAPI registra los paths **sin** `/mock`: por ejemplo, registra `/tickets`, aunque el navegador llame a `/mock/tickets`.

## Endpoints que necesita el frontend

Crear los mismos cinco endpoints para cada recurso:

| Metodo | Tickets | Activos | Proveedores | Funcion |
| --- | --- | --- | --- | --- |
| `GET` | `/tickets` | `/assets` | `/vendors` | Listado y datos del dashboard |
| `POST` | `/tickets` | `/assets` | `/vendors` | Crear registro |
| `GET` | `/tickets/{id}` | `/assets/{id}` | `/vendors/{id}` | Detalle y carga de edicion |
| `PATCH` | `/tickets/{id}` | `/assets/{id}` | `/vendors/{id}` | Actualizar registro |
| `DELETE` | `/tickets/{id}` | `/assets/{id}` | `/vendors/{id}` | Eliminar registro |

### Importante para el CRUD persistente de mockAPI

- El schema asociado a cada `GET /tickets`, `GET /assets` y `GET /vendors` debe devolver un **array de objetos**.
- Ese `GET` de coleccion permite que mockAPI inicialice y mantenga los items creados, editados o eliminados.
- Para los otros cuatro endpoints del recurso, usa un schema de **objeto individual** con los mismos campos.
- Todos los registros deben incluir `id`, porque la web lo usa para abrir detalle, editar y borrar.
- Los schemas siguientes incluyen `enum` para valores que la UI interpreta, `examples` para datos visibles realistas y `x-mock.pattern` solo para generar identificadores legibles. No necesitas configurar generadores.

Desde `/web/create_endpoint_form`, selecciona `Estructura de respuesta: Colección de objetos` y define sus campos para los endpoints `GET` de listado. La edición JSON avanzada del panel lateral solo hace falta para estructuras más anidadas.

## Forma general de respuestas

Listado:

```json
[
  { "id": "1", "status": "open" }
]
```

Detalle, alta o edicion:

```json
{ "id": "1", "status": "open" }
```

Eliminacion:

```json
{ "id": "1", "deleted": true }
```

Los formularios envian JSON con strings y omiten campos vacios.

## 1. Tickets

La web los usa en el dashboard, el listado y todo el flujo CRUD.

Schema de objeto para detalle, alta y edicion:

```json
{
  "type": "object",
  "properties": {
    "id": { "type": "string", "x-mock": { "pattern": "TCK-####" } },
    "title": {
      "type": "string",
      "examples": [
        "VPN access fails for remote employees",
        "Laptop provisioning blocked by approval",
        "Invoice export times out during month close"
      ]
    },
    "priority": { "type": "string", "enum": ["low", "normal", "high", "critical"] },
    "status": { "type": "string", "enum": ["open", "in_progress", "waiting", "closed"] },
    "queue": { "type": "string", "enum": ["Service Desk", "IT Operations", "Finance Ops", "Security Review"] },
    "assignee": { "type": "string", "examples": ["Alex Morgan", "Jordan Lee", "Robin Chen"] },
    "requester": { "type": "string", "examples": ["Taylor Brooks", "Sam Ortega"] },
    "description": {
      "type": "string",
      "examples": [
        "Users cannot connect after a credential rotation.",
        "The requested equipment cannot be assigned until approval is recorded."
      ]
    }
  }
}
```

El dashboard cuenta como abiertos `open`, `in_progress` y `waiting`; como prioritarios, `high` y `critical`.

## 2. Activos

Schema de objeto:

```json
{
  "type": "object",
  "properties": {
    "id": { "type": "string", "x-mock": { "pattern": "AST-###" } },
    "name": { "type": "string", "examples": ["Finance laptop", "Support workstation", "Meeting room tablet"] },
    "asset_tag": { "type": "string", "x-mock": { "pattern": "AS-#####" } },
    "status": { "type": "string", "enum": ["online", "offline", "maintenance", "assigned", "retired"] },
    "owner": { "type": "string", "examples": ["Jordan Lee", "Alex Morgan"] },
    "location": { "type": "string", "examples": ["Madrid HQ", "Barcelona Office"] },
    "serial": { "type": "string", "x-mock": { "pattern": "SN-########" } },
    "os": { "type": "string", "examples": ["Windows 11 Pro", "Ubuntu 24.04 LTS", "macOS 15"] }
  }
}
```

El dashboard cuenta como activos en servicio los estados `online` y `assigned`.

## 3. Proveedores

Schema de objeto:

```json
{
  "type": "object",
  "properties": {
    "id": { "type": "string", "x-mock": { "pattern": "VND-###" } },
    "name": { "type": "string", "examples": ["Northwind Systems", "BluePeak Hardware", "Cloud Harbor"] },
    "category": { "type": "string", "enum": ["hardware", "software", "cloud", "consulting", "support"] },
    "status": { "type": "string", "enum": ["active", "review", "blocked", "archived"] },
    "owner": { "type": "string", "examples": ["Morgan Rivera", "Alex Morgan"] },
    "contact_email": { "type": "string", "format": "email" },
    "phone": { "type": "string", "examples": ["+34 900 100 200", "+34 900 100 300"] },
    "notes": {
      "type": "string",
      "examples": ["SLA de sustitucion en 24 horas.", "Contrato pendiente de revision anual."]
    }
  }
}
```

El dashboard cuenta como proveedores activos solo los registros con `status: "active"`.

## Schema de coleccion

Para cada `GET` de listado, selecciona `Colección de objetos` en la interfaz. mockAPI generará una definición equivalente a:

```json
{
  "type": "array",
  "minItems": 4,
  "items": {
    "type": "object",
    "properties": {
      "id": { "type": "string" },
      "status": { "type": "string" }
    }
  }
}
```

Sustituye las propiedades del ejemplo por las del recurso completo: tickets, activos o proveedores.

## Orden recomendado de configuracion

1. Crear los tres schemas de coleccion y registrar `GET /tickets`, `GET /assets` y `GET /vendors`.
2. Crear los tres schemas de objeto y registrar los endpoints de detalle, alta, edicion y borrado.
3. Abrir Northstar y verificar los listados.
4. Probar el CRUD completo sobre tickets.
