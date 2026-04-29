# TA14-EcoTech

EcoTech is a frontend-focused e-waste awareness application built with Vue 3 and Vite. The current repository contains the web client, route structure, and a thin API layer that connects to a separately hosted backend service on Azure.

## Overview

The project is organized as a single-page application (SPA):

- `Vue 3` provides the component model and page rendering.
- `Vue Router` handles client-side navigation between feature pages.
- `Vite` handles local development, bundling, and module resolution.
- A small frontend API wrapper in `src/api/index.js` communicates with an external backend.

At the moment, the repository is frontend-heavy. Most feature pages are scaffolded as placeholders, while the `AI Chat` page is the only page that actively calls the backend API.

## Tech Stack

### Frontend

- Node.js `>=20.19.0`
- Vue `3.5.31`
- Vue Router `5.0.4`
- Vite `8.0.3`
- `@vitejs/plugin-vue` `6.0.5`

### Python Environment

- Python `>=3.10`
- `requests==2.32.3`

The Python virtual environment is local to the repo at `.venv/`. It is not used by the frontend app directly right now, but it is available for backend-related scripts, testing helpers, or future service integration work.

## Current Architecture

### High-level flow

1. The browser loads the Vite-built Vue application from `index.html`.
2. `src/main.js` creates the Vue app and installs the router.
3. `src/App.vue` renders the top navigation bar and the current route view.
4. `src/router/index.js` maps route paths to page-level Vue components.
5. Individual views render static content or call the shared API wrapper.
6. `src/api/index.js` sends HTTP requests to the external Azure backend.

### Text-based architecture graph

See [architecture.txt](/d:/26年课程/5120/project/group_repo/TA14-EcoTech/architecture.txt) for the standalone text graph. A copy is included below for convenience:

```text
Browser
  |
  v
index.html
  |
  v
src/main.js
  |
  v
Vue App (src/App.vue)
  |
  +--> Top Navigation
  |
  +--> Vue Router (src/router/index.js)
         |
         +--> /                   -> Home.vue
         +--> /dashboard          -> Dashboard.vue
         +--> /repair-check       -> RepairCheck.vue
         +--> /extend-usage       -> ExtendUsage.vue
         +--> /ai-chat            -> AIChat.vue
         +--> /safe-guidance      -> SafeGuidance.vue
         +--> /disposal-locations -> DisposalLocations.vue
                                       |
                                       v
                                  Shared API layer
                                  (src/api/index.js)
                                       |
                                       v
          Azure-hosted backend: /api/GetPerson
```

## Frontend Structure

### App shell

- `src/main.js`: application bootstrap
- `src/App.vue`: global navigation shell and route outlet
- `src/router/index.js`: route registry

### Views

- `Home.vue`: landing page with hero section and links to core feature areas
- `Dashboard.vue`: placeholder page
- `RepairCheck.vue`: placeholder page
- `ExtendUsage.vue`: placeholder page
- `AIChat.vue`: active integration page that fetches backend data on mount
- `SafeGuidance.vue`: placeholder page
- `DisposalLocations.vue`: placeholder page

### API layer

- `src/api/index.js`: shared API wrapper with a fixed backend base URL

This is currently a very thin abstraction. There is no request interceptor, no global error handling layer, no schema validation, and no environment-based API configuration yet.

## Backend Architecture Status

The backend implementation is not present in this repository.

What we can confirm from the frontend code:

- The frontend expects a backend hosted at:
  `https://ta14-ecotech-backend-ecf9e5hca9fpf7da.australiaeast-01.azurewebsites.net/api`
- The currently used endpoint is `GET /GetPerson`
- The API is called with the browser `fetch()` API
- The response is expected to be JSON

What we cannot confirm from this repo alone:

- Backend framework or language
- Data model definitions
- Authentication and authorization rules
- Database/storage design
- Input validation rules
- Rate limiting, logging, or deployment pipeline details

## Interface Design

### Implemented frontend-to-backend interface

Current shared API wrapper:

- Module: `src/api/index.js`
- Base URL: `/api` namespace on the Azure backend
- Style: plain async functions returning parsed JSON

Implemented operation:

| Frontend method | HTTP method | Backend path | Called from | Expected result |
| --- | --- | --- | --- | --- |
| `api.getPerson()` | `GET` | `/GetPerson` | `src/views/AIChat.vue` | JSON payload rendered directly in the page |

### Request/response behavior

- The frontend sends a simple `GET` request.
- No request body is included.
- No custom headers are added.
- Non-2xx responses throw an error in `src/api/index.js`.
- The success payload is passed straight to the Vue component without transformation.

### Current interface design characteristics

- Tight coupling to a hard-coded production-like backend URL
- No environment-specific configuration such as `.env`
- No typed response contract
- No retry, timeout, or loading-state abstraction
- No centralized error UI

This means the current interface layer is sufficient for a prototype, but still minimal for a production-grade frontend-backend contract.

## Architectural Assessment

### Strengths

- Simple and easy to understand structure
- Clear separation between routing, views, and API wrapper
- Good starting point for rapid feature iteration
- External backend integration is already wired into the frontend

### Current limitations

- Backend source code is not colocated with the frontend
- Most feature pages are placeholders and not yet connected to real logic
- API base URL is hard-coded instead of environment-driven
- No shared state management for cross-page data
- No API contract documentation beyond the single wrapper function
- No visible test coverage in the repository

## Local Development

### Install frontend dependencies

```sh
npm install
```

### Run the frontend

```sh
npm run dev
```

### Build for production

```sh
npm run build
```

### Lint

```sh
npm run lint
```

### Use the local Python virtual environment

PowerShell:

```powershell
cd d:\26年课程\5120\project\group_repo\TA14-EcoTech
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Or call the interpreter directly:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip show requests
```

## Suggested Next Steps

- Move the backend base URL into environment variables
- Expand the API layer to cover each feature page with named domain methods
- Define response schemas or TypeScript types for backend contracts
- Add loading, error, and empty-state handling in `AIChat.vue`
- Document or import the backend service source so frontend-backend integration is easier to maintain


## quiz start up
cd D:\26年课程\5120\project\group_repo\TA14-EcoTech
npm.cmd run dev
