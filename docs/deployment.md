# Deployment Guide — Azure → AWS

This walks through everything needed to take the project from local dev to live on AWS. Follow the steps in order.

## Prerequisites

- AWS account (free tier is enough for everything below).
- AWS CLI installed and configured (`aws configure`).
- A GitHub repo containing this project.
- Local Python 3.11+ and Node 20+.

---

## Step 1 — Run everything locally first

Get the system working end-to-end on your laptop before touching AWS.

### 1.1 Database (local Postgres)
```bash
# Mac:        brew install postgresql && brew services start postgresql
# Ubuntu:     sudo apt install postgresql && sudo systemctl start postgresql
# Windows:    install from https://www.postgresql.org/download/windows/

createdb ecotech
createuser -P ecotech_user      # set a password when prompted
psql ecotech -c "GRANT ALL PRIVILEGES ON DATABASE ecotech TO ecotech_user;"

psql -U ecotech_user -d ecotech -f database/schema/create_tables.sql
```

### 1.2 Load seed data
```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install pandas                                    # only needed for import scripts

cd ../database/import_scripts
python import_health.py
python import_emissions.py
python import_disposal.py
```

### 1.3 Run the backend
```bash
cd backend
python app.py        # listens on http://localhost:8000
```
Test: `curl http://localhost:8000/api/health` → `{"status":"ok"}`

### 1.4 Run the frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

If the dashboard loads with charts and the disposal map shows pins, you're done with local dev.

---

## Step 2 — Create RDS PostgreSQL

1. AWS Console → **RDS** → Create database.
2. Engine: PostgreSQL 16. Template: **Free tier**.
3. Identifier: `ecotech-db`. Master user: `ecotech_admin`. Password: store somewhere safe.
4. Instance: `db.t4g.micro`. Storage: 20 GB GP3.
5. **Public access: Yes** (only during dev — switch off later).
6. VPC security group: create new, add inbound rule allowing your IP on port 5432.
7. Initial database name: `ecotech`. Create.
8. Wait ~5 minutes for status `Available`. Copy the **endpoint** hostname.

### Run schema + load seeds against RDS
```bash
export DB_HOST=<rds-endpoint>
export DB_PORT=5432
export DB_NAME=ecotech
export DB_USER=ecotech_admin
export DB_PASSWORD=<your-password>

psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f database/schema/create_tables.sql
cd database/import_scripts
python import_health.py
python import_emissions.py
python import_disposal.py
```

---

## Step 3 — Deploy backend to Elastic Beanstalk

### 3.1 Install the EB CLI
```bash
pip install awsebcli
```

### 3.2 Initialise EB
```bash
cd backend
eb init -p python-3.11 ecotech-backend --region ap-southeast-2
eb create ecotech-backend-prod --single
```
`--single` skips the load balancer (cheaper for student/demo).

### 3.3 Set env vars on the EB environment
```bash
eb setenv \
  DB_HOST=<rds-endpoint> \
  DB_PORT=5432 \
  DB_NAME=ecotech \
  DB_USER=ecotech_admin \
  DB_PASSWORD=<your-password> \
  CORS_ORIGINS=https://<your-amplify-domain>.amplifyapp.com \
  FLASK_ENV=production
```

### 3.4 Tell EB how to run the app
Beanstalk's Python platform auto-detects `application` or `app` in `app.py`. We exposed `app = create_app()`, so it picks it up. To force gunicorn explicitly, add a file at `backend/Procfile`:
```
web: gunicorn app:app --bind 0.0.0.0:8000 --workers 2 --timeout 60
```

### 3.5 Deploy
```bash
eb deploy
eb open
```

You should see `{"service":"ecotech-backend","status":"ok"}` at the EB URL.

### 3.6 Allow EB to reach RDS
In RDS → security group, add inbound rule on port 5432 with source = the EB instance's security group.

---

## Step 4 — Deploy frontend to Amplify

1. AWS Console → **Amplify** → New app → Host web app → connect your GitHub repo.
2. Branch: `main`. Root directory: `frontend`.
3. Build settings — Amplify auto-detects Vite. If not, paste:
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands: [cd frontend, npm ci]
       build:
         commands: [cd frontend, npm run build]
     artifacts:
       baseDirectory: frontend/dist
       files: ['**/*']
     cache:
       paths: [frontend/node_modules/**/*]
   ```
4. Environment variables:
   - `VITE_API_SITE` = `https://<your-eb-app>.<region>.elasticbeanstalk.com/api`
5. Save and deploy.

---

## Step 5 — Verify end-to-end

1. Open the Amplify URL.
2. Network tab — every `/api/*` call should return 200, no CORS errors.
3. Dashboard renders charts. Disposal map shows pins. AI Chat returns tips.

---

## Step 6 — Lock things down before submission

- RDS → set Public Access **No**. Confirm only EB's security group can reach 5432.
- Backend `CORS_ORIGINS` → set to the exact Amplify domain (no `*`).
- Add an ACM TLS cert to the EB environment so the API serves HTTPS (avoids browser mixed-content warnings).
- Rotate the RDS master password and re-set it via `eb setenv`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Failed to fetch` in browser | `VITE_API_SITE` not set in Amplify, or backend CORS rejects the origin. |
| 502 on Beanstalk | gunicorn crashed on startup. `eb logs` and look for the traceback — usually missing env vars. |
| `psycopg2.OperationalError: timeout` | RDS security group doesn't allow EB. Add EB's SG as inbound source. |
| Mixed-content warning | Frontend on HTTPS, API on HTTP. Add ACM cert to EB. |
| `npm run build` fails on Amplify | Check Node version under app settings — set to 20. |
