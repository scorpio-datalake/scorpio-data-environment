# Scorpio Web UI (`web/` — Epic 7 scaffold)

Production-style **React + Material UI + Vite** shell with routes for SQL workspace, async jobs, session lifecycle, and a linear “notebook scratch” that issues coordinator SQL (**no** Jupyter protocol—see UX note below).

## Run locally (`npm`)

```shell
cd web
npm install
cp .env.example .env.development.local   # edit coordinator URL / tenant / bearer if needed
npm run dev                               # → http://127.0.0.1:5173/
```

Production bundle: **`npm run build`** → **`dist/`** (served behind your ingress or CDN).

### Environment (`VITE_*`)

| Variable | Purpose |
|---------|---------|
| `VITE_SCORPIO_COORDINATOR_URL` | Base URL matching **`docs/openapi/coordinator-v1.json`** paths |
| `VITE_SCORPIO_TENANT_ID` | Optional `X-Scorpio-Tenant-Id` |
| `VITE_SCORPIO_AUTH_BEARER` | Optional `Authorization: Bearer …` |

**CORS:** Browsers enforce same-origin unless the coordinator emits permissive **`Access-Control-*`** headers. For production place the UI behind a reverse proxy terminating on the coordinator host namespace, or implement coordinator CORS in **Phase 2** **`Planning/Phase2-OSS.md` P2‑E1**.

## Notebook UX (kernel vs gateway)

- **Notebook scratch Ep7 UI:** Executes **SQL-only** rows against **`POST /v1/sql`** (Arrow IPC payloads surface as binary-size hints until you add **`apache-arrow` JS decoding**).
- **Platform Jupyter path:** Hosted notebooks should use the **same coordinator** endpoints via **`python/scorpio`** (**Scorpio's Python API**) inside the platform Python image—for **`DataFrame`**, **`register_*`**, and future UDF plumbing.

## Wiring

REST calls live in **`src/api/coordinator.ts`**, keyed to OpenAPI v1 routes. Extend alongside **`Planning/Phase1.md` Epic 8** / **`Planning/Phase2-OSS.md` P2‑E1**.

## Licence

Apache License 2.0 — aligned with Scorpio **`LICENSE`** at repository root (`web/` bundles no standalone third-party license file beyond NPM package manifests).
