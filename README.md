# NBA & WNBA Data Project

Proyeccto de Data Engineergin orientado a construir progresivamente un plataforma de datos para NBA y WNBA.

---

## Current Status

Actualmente el proyecto se encuentra en las primeras etapas:
* Fase 0 - Project Foundation
* Fase 1 - Raw Data Ingestion

La ingesta RAW de juegos NBA desde BALLDONTLIE ya permite:

- Extraer datos reales desde una API externa.
- Limitar extracciones históricas mediante start_date y end_date.
- Navegar resultados mediante cursor-based pagination.
- Persistir cada página como un archivo RAW independiente.
- Conservar la respuesta original de la fuente junto con metadata técnica de ingestión.
- Manejar rate limiting mediante información proporcionada por los headers HTTP.
- Recuperarse de respuestas HTTP 429 y continuar desde el mismo cursor.

La última prueba integral realizó una extracción histórica de aproximadamente seis meses:

- 9 páginas.
- 825 juegos.
- Recuperación exitosa después de alcanzar el rate limit.

El siguiente checkpoint es realizar Data Profiling sobre los archivos RAW generados antes de avanzar hacia un historical backfill completo.

## Data Source

### BALLDONTLIE

Configuración actual:

* League: NBA
* Entity: games
* Pagination: cursor-based
* per_page = 100

## Repository Structure

```
nba-wnba-data-platform/
|
├── src/
|   └── ingestion/
|
├── data/
|   └── raw/
|       └── balldontlie/
|           └── nba/
|               └── games/
|
├── .gitignore
├── requirements.txt
└── README.md
```

`src/ingestion/`

* Contiene los mecanismos responsables de comunicarse con fuentes externas y administrar el flujo de extracción.

`data/raw/`

* Contiene las respuestas obtenidas desde las fuentes externas.
* Cada página extraída se almacena como un RAW independiente.
* Los archivos de datos raw no se versionan en Git.

#### Extracción Metadata

Cada archivo RAW utiliza actualmente un envelope con dos secciones:

```
RAW DOCUMENT
│
├── ingestion_metadata
│
└── source_response
    ├── data
    └── meta
```

`ingestion_metadata`: contiene información técnica de la extracción:
* source
* league
* entity
* endpoint
* extracted_at_utc
* http_status_code
* records_received
* min_game_date
* max_game_date

`source_response`: conserva la respuesta recibida desde BALLDONTLIE sin mezclarla con la metadata interna del pipeline.

## Pagination & Rate Limiting

La extracción utiliza start_date y end_date para definir el rango histórico y next_cursor para recorrer todas las páginas disponibles dentro de ese rango.

El cursor solamente avanza después de una respuesta exitosa. El flujo también inspecciona headers de rate limiting como:

* x-ratelimit-limit
* x-ratelimit-remaining
* x-ratelimit-reset
* Retry-After

Cuando el rate limit se alcanza, la extracción espera el tiempo indicado por la API y posteriormente reintenta la misma request sin perder el estado de paginación.


## Roadmap del Proyecto

- Fase 0 — Project Foundation 
- Fase 1 — Raw Data Ingestion 
- Fase 2 — Data Quality & Staging 
- Fase 3 — GCP Infrastructure 
- Fase 4 — Data Warehouse 
- Fase 5 — SQL Analytics Layer 
- Fase 6 — Orchestration & Productionization 
- Fase 7 — Testing & Observability 
- Fase 8 — Serving & Machine Learning
