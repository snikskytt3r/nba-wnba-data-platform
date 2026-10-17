# NBA & WNBA Data Project

Proyeccto de Data Engineergin orientado a construir progresivamente un plataforma de datos para NBA y WNBA.

## Current Status

Actualmente el proyecto tiene cerradas:

* Fase 0 - Project Foundation ✅
* Fase 1 - Raw Data Ingestion ✅

La Fase 1 cubre exclusivamente:

* League: NBA
* Source: BALLDONTLIE
* Entity: games
* Endpoint: `/v1/games`

La ingesta RAW de juegos NBA permite:

- Extraer datos reales desde una API externa.
- Limitar extracciones mediante `start_date` y `end_date`.
- Navegar resultados mediante cursor-based pagination.
- Persistir cada página como un archivo RAW independiente.
- Conservar la respuesta original de la fuente junto con metadata técnica de ingestión.
- Manejar rate limiting mediante información proporcionada por los headers HTTP.
- Recuperarse de respuestas HTTP 429 mediante retries acotados y continuar desde el mismo cursor.
- Ejecutar un historical backfill por unidades mensuales.
- Continuar mediante incremental ingestion usando un persisted state.
- Detectar ejecuciones NO-OP sin requests ni modificación del state.

Updates & Safe Re-execution permanece diferido como hardening backlog.

## Data Source

### BALLDONTLIE

Configuración actual:

* League: NBA
* Entity: games
* Endpoint: `/v1/games`
* Pagination: cursor-based
* `per_page = 100`

## Repository Structure

```text
nba-data-platform/
|
├── src/
|   ├── ingestion.py
|   ├── balldontlie.py
|   ├── extraction_scope.py
|   ├── raw_storage.py
|   └── state_storage.py
|
├── data/
|   └── raw/
|       └── balldontlie/
|           └── nba/
|               └── games/
|
├── state/
|   └── nba_incremental_state.json
|
├── .gitignore
├── requirements.txt
└── README.md
```

`ingestion.py`

* Orquesta el flujo completo de ingestión.
* Decide cuándo existe una ventana incremental, coordina sus unidades, consolida métricas y determina si corresponde persistir un nuevo boundary.

`balldontlie.py`

* Contiene la comunicación y extracción específica de BALLDONTLIE.
* Administra requests, cursor pagination, rate limiting, retries y el resultado de cada unidad.

`extraction_scope.py`

* Contiene los cálculos temporales necesarios para determinar el scope incremental y generar intervalos mensuales.

`raw_storage.py`

* Construye el documento RAW y persiste cada página recibida desde la fuente.

`state_storage.py`

* Lee y persiste el incremental state.
* Conoce cómo persistir el state; `ingestion.py` decide cuándo hacerlo.

`data/raw/`

* Contiene las respuestas obtenidas desde la fuente.
* Cada página extraída se almacena como un RAW independiente.
* Los archivos RAW no se versionan en Git.

## RAW Data Contract

Cada archivo RAW utiliza un envelope con dos secciones:

```text
RAW DOCUMENT
│
├── ingestion_metadata
│
└── source_response
    ├── data
    └── meta
```

`ingestion_metadata` contiene información técnica de la extracción:

* source
* league
* entity
* endpoint
* extracted_at_utc
* http_status_code
* records_received
* min_game_date
* max_game_date

`source_response` conserva la respuesta recibida desde BALLDONTLIE sin mezclarla con la metadata interna del pipeline.

Cada record dentro de `source_response.data` representa un game.

Naming actual:

```text
games_{season}_{start_date}_{end_date}_page_{page_count}.json
```

El historical backfill de Fase 1 cubrió la temporada competitiva NBA 2025-2026 excluyendo preseason. La única source of truth temporal persistida es:

```text
last_completed_boundary
```

El siguiente rango se determina mediante:

```text
next_start_date = last_completed_boundary + 1 day
cutoff = current_day - 1 day
```

Si: `next_start_date <= cutoff` se procesa la ventana: `[next_start_date, cutoff]`

Si no existe una ventana pendiente, la ejecución es NO-OP:

* no realiza requests;
* no genera unidades;
* no modifica el persisted state.

Una ventana procesada correctamente puede contener 0 games. Un successful empty window sigue siendo una ejecución válida.

## Persisted State Contract

El incremental state se almacena en:

```text
state/nba_incremental_state.json
```

Estructura:

```json
{
    "last_completed_boundary": "YYYY-MM-DD"
}
```

Si el archivo no existe, se utiliza el bootstrap boundary. Si el state existe pero no puede interpretarse correctamente, la ejecución se detiene y requiere revisión manual. La escritura se realiza primero sobre un archivo temporal y posteriormente se reemplaza el state definitivo.

`last_completed_boundary` sólo cambia en memoria después de persistir correctamente el nuevo state.

## Pagination & Rate Limiting

La extracción utiliza `start_date` y `end_date` para definir cada rango y `next_cursor` para recorrer todas las páginas disponibles dentro de ese rango.

El flujo inspecciona headers de rate limiting como:

* `x-ratelimit-limit`
* `x-ratelimit-remaining`
* `x-ratelimit-reset`
* `Retry-After`

El cursor se conserva durante un retry.

Cuando se recibe HTTP 429, la extracción utiliza `Retry-After` cuando está disponible. Si no existe, intenta calcular la espera mediante `x-ratelimit-reset`. Los retries están acotados.

También existe una espera preventiva cuando una respuesta exitosa informa que el rate limit disponible llegó a cero.

## Known Limitations

Updates & Safe Re-execution permanece. No están resueltos todavía:

* mutable game updates;
* cambios posteriores como Scheduled → Final;
* lookback windows;
* safe re-execution;
* overwrite semantics;
* idempotency semantics;
* RAW preservation/versioning.

El naming actual puede provocar overwrite si se vuelve a ejecutar exactamente la misma combinación de:

* season;
* start_date;
* end_date;
* page number.

## Roadmap del Proyecto

- Fase 0 — Project Foundation ✅
- Fase 1 — Raw Data Ingestion ✅
- Fase 2 — Data Quality & Staging
- Fase 3 — GCP Infrastructure
- Fase 4 — Data Warehouse
- Fase 5 — SQL Analytics Layer
- Fase 6 — Orchestration & Productionization
- Fase 7 — Testing & Observability
- Fase 8 — Serving & Machine Learning