# 🚀 Vanta Billing System (Facturama Multiemisor)

Este repositorio contiene el **microservicio** de facturación electrónica de **Vanta Solutions**. Está diseñado como un sistema desacoplado para gestionar el ciclo fiscal de múltiples organizaciones (tenants) mediante la integración con Facturama.

---

## 🛠 Tech Stack

### Frontend (Microservicio)
- **Framework:** Vue 3 (Vite + TypeScript).
- **UI:** Tailwind CSS.
- **State Management:** Pinia.
- **Routing:** Vue Router.

### Backend (Microservicio)
- **Framework:** FastAPI (Asíncrono).
- **Arquitectura:** Vertical Slice Architecture (VSA).
- **DB:** PostgreSQL en Neon (Shared Schema + `organization_id`).
- **Integración:** Facturama API (Modelo Multiemisor).

---

## 🏗 Arquitectura del Sistema

### 1. Backend: Vertical Slices
Cada funcionalidad es un "Slice" independiente que contiene su lógica, modelos y endpoints:
- `emisores/`: Alta de CSD (.cer, .key) y validación ante el SAT.
- `facturacion/`: Generación de CFDI 4.0, timbrado y almacenamiento.
- `catalogos/`: Proxy para búsqueda de claves Prod/Serv y unidades del SAT.

### 2. Frontend: Módulos Clave
El front se divide en cuatro áreas críticas para la gestión fiscal:

#### A. Configuración Fiscal (Onboarding)
- **Carga de Sellos:** Interfaz para subir certificados CSD con validación de vigencia inmediata.
- **Perfil del Emisor:** Gestión de RFC, Razón Social y Régimen Fiscal.

#### B. Generador de CFDI 4.0 (Smart Form)
- **Buscador Proactivo:** Input de búsqueda para claves SAT con auto-completado.
- **Cálculo Automático:** Desglose de IVA, Retenciones e IEPS en tiempo real mientras se agregan conceptos.
- **Preview de Factura:** Generación de una vista previa (Borrador) antes de consumir un timbre.

#### C. Explorador de Comprobantes
- **Gestión Documental:** Tabla con filtros avanzados por fecha, cliente y estado de timbrado.
- **Acciones Rápidas:** Descarga de XML/PDF y reenvío de facturas por email con un clic.
- **Módulo de Cancelación:** Flujo guiado para seleccionar el motivo de cancelación (01-04) según las reglas del SAT.

#### D. Monitor de Consumo
- **Dashboard de Timbres:** Visualización de folios disponibles y gráficas de facturación mensual por organización.

---

## 🔑 Estrategia Multitenant

El sistema garantiza el aislamiento de datos mediante:
1. **Contexto de Organización:** El Frontend envía el `organization_id` en los headers de cada petición.
2. **Seguridad en DB:** El Backend aplica un filtro global en todas las queries de SQLAlchemy para asegurar que los usuarios solo vean documentos de su propia empresa.

---

## 🗺 Roadmap de Implementación

- [x] **Fase 1:** Setup de FastAPI + Middleware de Multitenancy + Conexión a Neon.
- [ ] **Fase 2:** Cliente de Facturama y módulo de carga de CSD (Back + Front).
- [ ] **Fase 3:** Formulario de emisión de facturas con validación.
- [ ] **Fase 4:** Explorador de facturas con descarga de archivos y flujo de cancelación.
- [ ] **Fase 5:** Integración vía API Key para servicios externos.

---

## 🚀 Guía de Inicio Rápido

1. **Backend:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend:**
   ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```
