# EcoTech

E-waste awareness platform connecting **pollution data**, **health impact**, and **action** (disposal locations, repair/reuse guidance).

```
ecotech/
├── frontend/      Vue 3 + Vite SPA     (deploys to AWS Amplify)
├── backend/       Flask + gunicorn API (deploys to AWS Elastic Beanstalk)
├── database/      PostgreSQL schema + seed CSVs + import scripts
└── docs/          architecture, API reference, deployment guide
```

## Stack

| Layer    | Tech                              | Hosted on              |
|----------|-----------------------------------|------------------------|
| Frontend | Vue 3, Vite, ECharts, Leaflet     | AWS Amplify            |
| Backend  | Flask, gunicorn, psycopg2          | AWS Elastic Beanstalk  |
| Database | PostgreSQL 16                     | AWS RDS                |

## Quick start (local)

```bash
# 1. Database
createdb ecotech
psql ecotech -f database/schema/create_tables.sql

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env .env.local        # then edit .env.local with your DB creds
python app.py             # http://localhost:8000

# 3. Seeds
cd ../database/import_scripts
python import_health.py
python import_emissions.py
python import_disposal.py

# 4. Frontend
cd ../../frontend
npm install
npm run dev               # http://localhost:5173
```

## Deploying to AWS

See `docs/deployment.md` for the full step-by-step guide (RDS → Beanstalk → Amplify → lock down). The TL;DR:

1. Create an RDS PostgreSQL instance, run `create_tables.sql`, run the three import scripts against it.
2. `eb init` + `eb create` + `eb setenv DB_HOST=...` + `eb deploy` from `backend/`.
3. Connect the Amplify console to the GitHub repo, set `VITE_API_SITE` to the EB URL.

## Endpoints

See `docs/api_endpoints.md`. Summary:

```
GET  /api/health/all
GET  /api/health/filters
GET  /api/emissions/state
GET  /api/emissions/facility
GET  /api/map/disposal-locations
GET  /api/map/disposal-locations/<postcode>
POST /api/ai/device-optimizer
```

## Project layout

See `docs/architecture.md` for the request-flow diagram and a per-folder explanation of why this layout was chosen.
