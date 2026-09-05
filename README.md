# NBA & WNBA Data Project

Proyeccto de Data Engineergin orientado a construir progresivamente un plataforma de datos para NBA y WNBA.

---

## Current Status

Actualmente el proyecto se encuentra en las primeras etapas:
* Fase 0 - Project Foundation
* Fase 1 - Raw Data Ingestion

El primer checkpoint funcional logró extraer datos reales de NBA desde una fuente externa, conservando la respuesta completa en almacenamiento raw y se hizo la primera inspección estructural.

## Data Source

### BALLDONTLIE

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

* Contiene los mecanismos responsables de comunicarse con fuentes externas y extraer datos.

`data/raw/`

* Contiene las respuestas obtenidas desde las fuentes externas.
* Los archivos de datos raw no se versionan en Git.

#### Extraction Metadata ✅

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
