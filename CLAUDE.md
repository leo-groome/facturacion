# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Vanta Billing System** — a multi-tenant electronic invoicing (facturación electrónica CFDI 4.0) microservice for Vanta Solutions, integrating with [Facturama API](https://facturama.mx) (Modelo Multiemisor) to manage the full fiscal cycle for multiple organizations.

Roadmap status: Phase 1 (Setup + Multitenancy) ✅ and Phase 2 (CSD Upload) ✅ are complete. Phases 3–5 are pending.

---

## Commands

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload         # Dev server on http://localhost:8000
uvicorn app.main:app --host 0.0.0.0 --port 8000  # Production
```

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
| `emisores/` | CSD (.cer/.key) upload, Fernet encryption, Facturama validation | ✅ Implemented |
| `facturacion/` | CFDI 4.0 generation, timbrado via Facturama, XML/PDF storage | Phase 3 |
| `catalogos/` | Read-only async proxy for SAT Prod/Serv + unit catalogs | Phase 3 |
| `auth/` | JWT / API Key middleware (`Depends`) | Phase 5 |
| `apikeys/` | API Key management (stored as bcrypt hash, shown once in clear) | Phase 5 |

Key files:
- `backend/app/main.py` — FastAPI app, CORS config, router registration
- `backend/app/slices/emisores/router.py` — `POST /api/v1/emisores/csd`
- `backend/app/slices/emisores/facturama_client.py` — async `httpx` client for Facturama

### Frontend — Vue 3 SPA

Four planned modules (mostly stubs until Phase 3+):

- **Onboarding Fiscal** — CSD upload, emisor profile (RFC, Razón Social, Régimen)
- **Generador CFDI 4.0** — Smart form with SAT catalog autocomplete, live IVA/IEPS/Retenciones calculation, invoice preview (draft, no timbre consumed)
- **Explorador de Comprobantes** — Data-grid with filters, XML/PDF download as Blob (never open-URL), cancelation wizard (motivos 01–04 SAT)
- **Monitor de Consumo** — Per-tenant credit/timbre usage dashboards

Key files:
- `frontend/src/main.ts` — Vue app entry, Pinia + Router setup
- `frontend/src/router/index.ts` — Vue Router (routes added per phase)
- `frontend/src/stores/` — Pinia stores (counter.ts is a demo placeholder)

### Multi-Tenancy

Shared Schema strategy: every DB table has an `organization_id` column. Every SQLAlchemy query must filter by `organization_id`. The frontend sends `organization_id` in Axios headers via a global interceptor that also injects the JWT from localStorage.

**IDOR prevention is mandatory:** always verify that the `organization_id` in the JWT matches the resource being accessed at the DB level.

---

## Environment Variables

Backend `.env` (never commit):

```
PGHOST / PGDATABASE / PGUSER / PGPASSWORD / PGSSLMODE   # Neon PostgreSQL
CSD_ENCRYPTION_KEY   # Fernet key for AES encryption of CSD files at rest
SECRET_KEY           # JWT signing secret
ALGORITHM            # HS256
ACCESS_TOKEN_EXPIRE_MINUTES  # 1440
FACTURAMA_API_URL    # https://apisandbox.facturama.mx (sandbox)
FACTURAMA_USER / FACTURAMA_PASSWORD
```

---

## Key Technical Rules

### Backend
- All endpoints and DB operations must be `async`/`await` (FastAPI + asyncpg + SQLAlchemy async).
- Use FastAPI `Depends` for DB session injection and JWT parsing — never instantiate manually inside route handlers.
- Use Pydantic models + SQLAlchemy ORM exclusively for data validation and DB access (no raw string concatenation for queries).
- Use `Decimal` for all monetary calculations — never `float`.
- `catalogos` slice must cache SAT catalog lookups to avoid Facturama rate limits.

### Frontend
- Use Composition API with `<script setup>` exclusively — Options API is prohibited.
- TypeScript strict mode is enabled (`noUncheckedIndexedAccess`). No `any` shortcuts.
- Cross-page state lives in Pinia stores.
- All SAT catalog search inputs must debounce network requests.
- File downloads (XML/PDF/ZIP) must use Axios Blob responses — never expose raw URLs.
- The invoice preview endpoint must not consume a real fiscal stamp (timbre).

### Phase-specific notes (Phases 3+)
- **Phase 3 — facturacion slice:** Implement async concurrency to Facturama for timbrado; provide a local validation/draft endpoint that does not consume timbres.
- **Phase 4 — cancelation:** Enumerate SAT motivos exactly as `01`, `02`, `03`, `04`; all explorer endpoints require pagination and mandatory `organization_id` filter.
- **Phase 5 — API Keys:** Validate via `x-api-key` custom header in a `Depends` middleware; store only the bcrypt hash in DB; display the raw key once on generation.
