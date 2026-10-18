# DataMind — Liquid Glass Frontend

The production-oriented React + Vite frontend for DataMind. It keeps the
liquid-glass visual language while rendering live backend evidence only:
schema metadata, generated SQL, Snowflake rows, explanations, assumptions,
warnings, query IDs, connection health, and local query history.

## Requirements

- Node.js 18+ (Node 20+ recommended)
- npm

## Run locally

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Start the FastAPI backend separately from the
repository root:

```powershell
D:\Projects\Hackobter\datamind\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The frontend defaults to `http://127.0.0.1:8000`. To override it, create
`datamind-liquid-glass-frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Build

```bash
npm run build
npm run preview
```

## Project structure

```text
src/
  main.jsx                 Entry: Router + Theme + Auth providers
  App.jsx                  Routes only (public /login, protected app routes)
  api/client.js            Typed fetch wrapper for the FastAPI backend
  context/                 Theme, auth, and live data/query-history contexts
  layouts/AppLayout.jsx    Sidebar, topbar, toast, activity modal
  pages/                   Login, Overview, AskData, Live, History, Sources
  components/              liquid.jsx (effects), PageKit.jsx, ThemeToggle.jsx
  styles.css  theme.css  auth.css
```

Theme: dark/light toggle in the topbar (and login page); saved in localStorage, follows system preference first.
Auth: local demo identity only. It does not provide backend authorization and
must not be treated as production authentication.

## Backend contract

The data context calls:

- `GET /health`
- `GET /api/schema`
- `POST /api/query` with `{ "question": "..." }`

The query result status can be `ok`, `empty`, `clarification_required`, or
`unsupported`. The UI renders each state explicitly. SQL validation and
Snowflake execution remain backend responsibilities.

The backend allows Vite origins by default. For another deployed origin, set
`DATAMIND_FRONTEND_ORIGINS` in the backend environment to a comma-separated
list of exact origins.

## Deployment

Build the static site:

```bash
npm run build
```

Deploy the generated `dist/` directory to any static host. Set
`VITE_API_BASE_URL` to the public HTTPS URL of the deployed FastAPI service
before building; Vite injects `VITE_*` values at build time.

### Azure Static Web Apps

1. Create a Static Web App connected to this repository.
2. Set the app location to `datamind-liquid-glass-frontend`.
3. Set the output location to `dist`.
4. Add `VITE_API_BASE_URL=https://<your-api-host>` as a build environment variable.
5. Set backend `DATAMIND_FRONTEND_ORIGINS=https://<your-static-app-host>`.
6. Deploy the FastAPI backend separately on Azure App Service, Container Apps,
   or another HTTPS Python host. Keep Snowflake and Google credentials only in
   backend environment settings.

### Vercel or Netlify

1. Import the repository and select `datamind-liquid-glass-frontend` as the
   project root.
2. Build command: `npm run build`.
3. Publish directory: `dist`.
4. Set `VITE_API_BASE_URL` to the public backend URL.
5. Add the deployed frontend origin to `DATAMIND_FRONTEND_ORIGINS`.

The frontend must use HTTPS when the backend is public HTTPS; browsers block
mixed-content requests from an HTTPS frontend to an HTTP API.

The UI retains the reference's dark palette, glass surfaces, fine highlights,
lime accents, layered blur, and smooth motion, adapted for live DataMind
evidence. No analytics numbers or SQL are fabricated in the frontend.
