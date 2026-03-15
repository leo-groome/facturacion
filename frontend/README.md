# Vanta Billing Frontend (Microservicio)

Este es el frontend del microservicio de facturación electrónica de Vanta Solutions, construido con Vue 3 y Tailwind CSS.

## Tech Stack

- **Vue 3** (Composition API)
- **Vite** (Build Tool)
- **Tailwind CSS** (Styling)
- **Pinia** (State Management)
- **Vue Router** (Routing)
- **TypeScript** (Type Safety)

## Project Setup

```sh
pnpm install
```

### Compile and Hot-Reload for Development

```sh
pnpm dev
```

### Type-Check, Compile and Minify for Production

```sh
pnpm build
```

### Run Unit Tests with Vitest

```sh
pnpm test:unit
```

### Lint and Format

```sh
pnpm lint
pnpm format
```

## Estructura de Módulos

- `src/views/`: Vistas principales (Emisión, Explorador, Configuración).
- `src/components/`: Componentes reutilizables de UI.
- `src/stores/`: Lógica de estado global (auth, tenant, catálogos).
- `src/services/`: Integración con el API de Backend.
