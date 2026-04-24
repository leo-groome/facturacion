# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Vanta Billing System** — a multi-tenant electronic invoicing (CFDI 4.0) microservice for Vanta Solutions, integrating with [Facturama API](https://facturama.mx) (Modelo Multiemisor) to manage the full fiscal cycle for multiple organizations.

All 5 phases are implemented and functional.

---

## Commands

### Backend

```bash
cd backend
py -3.12 -m venv venv              # Requiere Python 3.12
source venv/bin/activate            # Linux/Mac
venv\Scripts\activate               # Windows
pip install -r requirements.txt
python run.py                       # Dev server on http://localhost:8000 (OBLIGATORIO en Windows)
```

> **IMPORTANTE (Windows):** Siempre usar `python run.py`, NUNCA `uvicorn app.main:app --reload`.
> `run.py` fija `SelectorEventLoop` antes de que uvicorn arranque. Sin esto, psycopg3 no puede
> conectarse a PostgreSQL y todas las operaciones de BD fallan silenciosamente.

### Frontend

```bash
cd frontend
pnpm install
pnpm dev           # Dev server on http://localhost:5173
pnpm build         # Type-check + Vite build
pnpm type-check    # vue-tsc --build
pnpm test:unit     # Vitest
pnpm lint          # oxlint + eslint --fix
pnpm format        # Prettier --write
```

---

## Architecture

### Backend — Vertical Slice Architecture (VSA)

**Non-negotiable rule:** the backend is organized by business feature ("Slice"), not by technical layer. Each slice under `backend/app/slices/` is fully self-contained with its own Pydantic schemas, business logic, and FastAPI router. Creating omnipotent utility files that span slices is prohibited.

| Slice | Purpose | Status |
|---|---|---|
| `auth/` | JWT authentication (signup/login), middleware de rechazo temprano | Implemented |
| `emisores/` | CSD (.cer/.key) upload, Fernet encryption, Facturama sync | Implemented |
| `facturacion/` | CFDI 4.0 preview/emision/descarga/cancelacion via Facturama | Implemented |
| `catalogos/` | Read-only async proxy for SAT catalogs (ProdServ, Unidades, FormasPago, etc.) with 30min TTL cache | Implemented |
| `apikeys/` | API Key management (bcrypt hash, shown once, rate limited 100 req/min) | Implemented |

Key files:
- `backend/run.py` — Launcher que fija SelectorEventLoop en Windows antes de uvicorn
- `backend/app/main.py` — FastAPI app, CORS config, middleware, router registration
- `backend/app/core/dependencies.py` — `get_current_tenant()` dependency (JWT validation + IDOR prevention)
- `backend/app/core/database.py` — Async connection pool (psycopg3 + Neon)
- `backend/app/slices/facturacion/schema.py` — Pydantic schemas for CFDI 4.0
- `backend/app/slices/emisores/facturama_client.py` — async `httpx` client for Facturama
- `backend/setup_db.py` — DDL script for table creation

### Frontend — Vue 3 SPA

| Module | Route | Component | Purpose |
|---|---|---|---|
| Auth | `/login` | `AuthView.vue` | Login/signup con validacion RFC |
| Onboarding | `/onboarding` | `OnboardingView.vue` → `CsdUploader.vue` | CSD upload (.cer/.key) |
| Emision | `/emision` | `EmisionView.vue` → `SmartForm.vue` | Generador CFDI 4.0 con catalogo SAT |
| Explorador | `/explorador` | `ExploradorView.vue` → `DataGrid.vue` + `CancellationModal.vue` | Lista facturas, descarga, cancelacion |
| API Keys | `/apikeys` | `ApiKeysView.vue` → `KeyManager.vue` | Gestion de API Keys B2B |

Key files:
- `frontend/src/services/api.ts` — Axios instance con interceptor JWT y manejo de 401
- `frontend/src/stores/auth.ts` — Pinia store para JWT, login/signup
- `frontend/src/stores/facturacion.ts` — Pinia store para conceptos, calculos IVA/IEPS/Retenciones

### Multi-Tenancy

Shared Schema strategy: every DB table has an `organization_id` column. Every psycopg query filters by `organization_id` extracted from the JWT (never from client headers). The frontend injects the JWT via Axios interceptor.

**IDOR prevention is mandatory:** the `organization_id` comes exclusively from `get_current_tenant()` which extracts it from the signed JWT — never from request params or headers.

---

## Database Tables (Neon PostgreSQL)

- `clientes` — Tenants (id UUID, nombre_empresa, rfc UNIQUE, contrasena bcrypt)
- `emisores` — CSD certificates per tenant (cer/key/password encrypted with Fernet)
- `facturas` — Invoices (folio_fiscal, facturama_id, receptor_*, totals, estado, xml_content)
- `api_keys` — B2B keys (prefix, hashed_key bcrypt, activa)

### Migraciones de schema

`backend/setup_db.py` es el único DDL versionado. Usa `CREATE TABLE IF NOT EXISTS` (idempotente, seguro de re-ejecutar), pero **no hay sistema de migraciones** (Alembic no está configurado). Consecuencias:

- Al cambiar una columna existente hay que aplicar el DDL manualmente en Neon antes de correr la app, y reflejar el cambio en `setup_db.py` para nuevos despliegues.
- No hay rollback automático. Antes de cambios destructivos (drop/alter), respaldar la tabla afectada.
- Si el proyecto crece, evaluar migrar a Alembic.

## Environment Variables

Backend `.env` (never commit):

```
PGHOST / PGDATABASE / PGUSER / PGPASSWORD / PGSSLMODE   # Neon PostgreSQL
CSD_ENCRYPTION_KEY   # Fernet key for AES encryption of CSD files at rest
SECRET_KEY           # JWT signing secret (32+ chars)
ALGORITHM            # HS256
ACCESS_TOKEN_EXPIRE_MINUTES  # 1440 (24h)
FACTURAMA_API_URL    # https://apisandbox.facturama.mx (sandbox)
FACTURAMA_USER / FACTURAMA_PASSWORD
ALLOWED_ORIGINS      # http://localhost:5173 (default)
APP_ENV              # development | production (production disables /docs)
```

---

## Key Technical Rules

### Backend
- All endpoints and DB operations must be `async`/`await` (FastAPI + psycopg3 async).
- Use FastAPI `Depends` for DB session injection and JWT parsing — never instantiate manually.
- Use `Decimal` for all monetary calculations — never `float`.
- `catalogos` slice caches SAT catalog lookups (30min TTL) to avoid Facturama rate limits.
- Error handlers must differentiate DB connection errors from business logic errors (never catch all exceptions as a single error type).

### Frontend
- Use Composition API with `<script setup>` exclusively — Options API is prohibited.
- TypeScript strict mode is enabled (`noUncheckedIndexedAccess`). No `any` shortcuts.
- Cross-page state lives in Pinia stores.
- All SAT catalog search inputs must debounce network requests (500ms).
- File downloads (XML/PDF/ZIP) must use Axios Blob responses — never expose raw URLs.
- The invoice preview endpoint must not consume a real fiscal stamp (timbre).
- Backend returns `estado: "Vigente" | "Cancelado"` — frontend must match these exact strings.
