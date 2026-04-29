# EcoTech Architecture

## High-level diagram

```
                      ┌──────────────────────────┐
                      │   User's browser          │
                      └────────────┬─────────────┘
                                   │  HTTPS
                                   ▼
                      ┌──────────────────────────┐
                      │  AWS Amplify (Frontend)   │
                      │  Vue 3 + Vite static SPA  │
                      └────────────┬─────────────┘
                                   │  HTTPS  /api/*
                                   ▼
                      ┌──────────────────────────┐
                      │  AWS Elastic Beanstalk    │
                      │  Flask + gunicorn         │
                      └────────────┬─────────────┘
                                   │  TCP 5432 (VPC private)
                                   ▼
                      ┌──────────────────────────┐
                      │  AWS RDS PostgreSQL       │
                      │  health_merged            │
                      │  heavy_metal_state        │
                      │  heavy_metal_facility     │
                      │  ewaste_facilities        │
                      └──────────────────────────┘
```

## Components

**Frontend (Vue 3, Vite)** — single-page app. Uses `vue-router` for client-side routing and ECharts + Leaflet for visualisations. The base URL of the backend is read from the `VITE_API_SITE` environment variable at build time, so the same source builds against local Flask in dev and the Beanstalk URL in prod.

**Backend (Flask, gunicorn)** — modular layout:

```
app.py                  Flask entry point + blueprint registration
config.py               env-var-driven config
routes/                 HTTP layer (parses request, calls service)
services/               business logic (calls queries, shapes response)
db/queries/             raw SQL strings, one file per domain
db/connection.py        psycopg2 connection pool + context manager
models/                 dataclasses that wrap DB rows
utils/                  helpers (response builders, validation)
```

This four-layer split (routes → services → queries → connection) means each layer has a single responsibility, so changes to one don't ripple through the rest.

**Database (PostgreSQL on RDS)** — four tables. Schema in `database/schema/create_tables.sql`. Forward migrations go in `alter_tables.sql`. Seeds come from cleaned CSVs and are loaded with the Python scripts in `database/import_scripts/`, which use `psycopg2.extras.execute_values` for fast batch inserts and avoid the 1000-row limit we hit on Azure.

## Request flow (example: `/api/emissions/state`)

1. Browser fetches `${VITE_API_SITE}/emissions/state`
2. Amplify CDN serves the static Vue bundle, which makes the cross-origin call
3. Beanstalk → gunicorn → `app.py` → `emissions_bp` blueprint
4. `routes/emissions_routes.py::by_state` calls `services/emissions_service.list_by_state()`
5. The service calls `db/queries/emissions_queries.SELECT_BY_STATE` through `db/connection.get_cursor()`
6. RDS returns rows; `EmissionStateRow.from_row(...)` shapes each row
7. JSON response goes back through the same path

## Why this layout

- **Testable** — services and queries can be unit-tested without a running web server.
- **Cloud-portable** — nothing in the code references AWS-specific services. Move from EB to ECS later by changing only the deployment, not the code.
- **Migration-safe** — switching DB columns means changing one query file and one model file, not seven route handlers.

## What lives where in AWS

| Concern | AWS service | Notes |
|---|---|---|
| Static frontend | Amplify | Auto-deploys on push to `main`. |
| API server | Elastic Beanstalk (Python platform) | Single-container, gunicorn. |
| Database | RDS PostgreSQL `db.t4g.micro` | Free-tier eligible. Public during dev, VPC-private after. |
| Secrets | EB env vars | Not committed. `.env` is for local only. |
| TLS / HTTPS | Amplify default + ACM cert on EB load balancer | |
| Logs | CloudWatch (auto from EB) | |
