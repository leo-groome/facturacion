# Vanta Billing System (Facturama Multiemisor)

Este repositorio contiene el **microservicio** de facturación electrónica de **Vanta Solutions**. Está diseñado como un sistema desacoplado para gestionar el ciclo fiscal de múltiples organizaciones (tenants) mediante la integración con Facturama.

---

## Tech Stack

### Frontend
- **Framework:** Vue 3 (Vite + TypeScript)
- **UI:** Tailwind CSS
- **State Management:** Pinia
- **Routing:** Vue Router

### Backend
- **Framework:** FastAPI (Asíncrono)
- **Arquitectura:** Vertical Slice Architecture (VSA)
- **DB:** PostgreSQL en Neon (Shared Schema + `organization_id`)
- **Driver:** psycopg3 (async) + psycopg-pool
- **Integración:** Facturama API (Modelo Multiemisor)
- **Auth:** JWT (PyJWT + bcrypt)
- **Cifrado:** Fernet (AES) para CSD en reposo

---

## Arquitectura del Sistema

### 1. Backend: Vertical Slices

Cada funcionalidad es un "Slice" independiente que contiene su lógica, modelos y endpoints:

| Slice | Descripción |
|---|---|
| `auth/` | Autenticación JWT (signup/login) + middleware de rechazo temprano |
| `emisores/` | Alta de CSD (.cer, .key), cifrado Fernet y sincronización con Facturama |
| `facturacion/` | Generación de CFDI 4.0, preview sin timbre, timbrado, descarga y cancelación |
| `catalogos/` | Proxy async hacia catálogos SAT de Facturama con cache TTL de 30 min |
| `apikeys/` | Gestión de API Keys B2B (bcrypt hash, se muestra una sola vez, rate limit 100 req/min) |

### 2. Frontend: Módulos

#### A. Autenticación
- Login y registro con validación de RFC mexicano.
- JWT almacenado en localStorage e inyectado automáticamente via interceptor Axios.

#### B. Configuración Fiscal (Onboarding)
- Carga de Sellos CSD (.cer + .key + contraseña).
- Cifrado en reposo con Fernet antes de persistir en BD.

#### C. Generador de CFDI 4.0 (Smart Form)
- Buscador predictivo de claves SAT con autocompletado (debounce 500ms).
- Selector de régimen fiscal (26 regímenes SAT), método de pago (PUE/PPD), forma de pago, moneda y correo del receptor.
- Cálculo automático de IVA, IEPS y retenciones en tiempo real.
- Vista previa (borrador) sin consumir timbre fiscal.

#### D. Explorador de Comprobantes
- Tabla paginada con filtros por estado (Vigente/Cancelado).
- Descarga segura de XML/PDF/ZIP via Blob (nunca URLs directas).
- Cancelación guiada con motivos SAT 01-04.

#### E. API Keys B2B
- Generación de API Keys con hash bcrypt (clave visible una sola vez).
- Listado de claves activas y revocación.

---

## Estrategia Multitenant

El aislamiento de datos se garantiza mediante:

1. **JWT como fuente de verdad:** El `organization_id` se extrae exclusivamente del token JWT firmado, nunca de headers del cliente.
2. **Filtro obligatorio en BD:** Todas las queries incluyen `WHERE organization_id = %s` usando el ID del JWT.
3. **Prevención de IDOR:** El backend valida la propiedad del recurso antes de servir datos o ejecutar acciones.

---

## Guía de Inicio Rápido

### Requisitos
- Python 3.12
- Node.js + pnpm
- PostgreSQL (Neon o local)

### 1. Backend

```bash
cd backend
py -3.12 -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

Crear archivo `.env` con las variables necesarias (ver `.env.example` o CLAUDE.md).

Inicializar la base de datos (solo la primera vez):
```bash
python setup_db.py
```

Arrancar el servidor:
```bash
python run.py
```

> **IMPORTANTE (Windows):** Siempre usar `python run.py`, NUNCA `uvicorn app.main:app --reload`.
> En Windows, uvicorn usa `ProactorEventLoop` por defecto, pero psycopg3 requiere `SelectorEventLoop`.
> `run.py` fija la política del event loop antes de que uvicorn arranque. Sin esto, todas las
> operaciones de base de datos fallan silenciosamente.

El servidor estará disponible en `http://localhost:8000`. Documentación interactiva en `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

El frontend estará disponible en `http://localhost:5173`.

---

## Roadmap de Implementación

- [x] **Fase 1:** Setup de FastAPI + Middleware de Multitenancy + Conexión a Neon.
- [x] **Fase 2:** Cliente de Facturama y módulo de carga de CSD (Back + Front).
- [x] **Fase 3:** Formulario de emisión de facturas con validación y preview.
- [x] **Fase 4:** Explorador de facturas con descarga de archivos y flujo de cancelación.
- [x] **Fase 5:** Autenticación JWT + API Keys B2B con rate limiting.
