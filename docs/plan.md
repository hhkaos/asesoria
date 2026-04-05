# Plan de Implementación — Plataforma de Asesoría Fiscal

> Para la especificación funcional completa ver [SPEC.md](../SPEC.md).
> Para convenciones técnicas, stack y decisiones de arquitectura ver [CLAUDE.md](../CLAUDE.md).

Este documento trackea el progreso de implementación fase a fase. Cada tarea se marca cuando está
completada y revisada con el equipo.

---

## Cómo trabajamos

- **Pair programming / human-in-the-loop**: antes de implementar cada fase, se presenta el plan
  detallado (qué ficheros, qué instala, qué decisiones toma) y se espera validación.
- **Una fase a la vez**: no se empieza la siguiente hasta que la anterior pasa todos los checks.
- **Checks de verificación**: cada fase tiene un listado de comprobaciones concretas para confirmar
  que todo funciona antes de avanzar.

---

## Fase 0 — Estructura base y entorno de desarrollo

**Objetivo:** que `docker compose up` arranque backend + frontend + postgres, la API responda en
`/health`, y los tests pasen. Sin lógica de negocio.

**Estado:** `pendiente`

### Qué se instala / arranca

| Servicio    | Cómo                       | Puerto local |
| ----------- | -------------------------- | ------------ |
| PostgreSQL 16 | Docker (imagen oficial)  | 5432         |
| PostgreSQL 16 (tests) | Docker            | 5433         |
| Backend FastAPI | Docker (Python 3.12)  | 8000         |
| Frontend React/Vite | Docker (Node 22)  | 5173         |

> No se instala nada en la máquina host excepto Docker Desktop.

### Ficheros a crear

**Raíz del monorepo**
- [ ] `.gitignore`
- [ ] `.env.example`
- [ ] `docker-compose.yml`
- [ ] `Makefile`

**Backend**
- [ ] `backend/pyproject.toml` (FastAPI, SQLAlchemy async, Alembic, pyotp, pytest…)
- [ ] `backend/app/core/config.py` (Settings con pydantic-settings)
- [ ] `backend/app/core/database.py` (engine async, Base, get_db)
- [ ] `backend/app/api/health.py` (GET /health)
- [ ] `backend/app/main.py`
- [ ] `backend/alembic/env.py` (configurado para async + autogenerate)
- [ ] `backend/tests/conftest.py`
- [ ] `backend/tests/integration/test_health.py`
- [ ] `backend/tests/unit/test_placeholder.py`
- [ ] `backend/Dockerfile`

**Frontend**
- [ ] `frontend/package.json` (React 18, Vite, Tailwind, Vitest, ESLint, Prettier)
- [ ] `frontend/vite.config.ts` (proxy `/api → backend:8000`)
- [ ] `frontend/tsconfig.json`
- [ ] `frontend/tailwind.config.js` + `postcss.config.js`
- [ ] `frontend/eslint.config.js` + `frontend/.prettierrc`
- [ ] `frontend/src/App.tsx` (pantalla "en construcción")
- [ ] `frontend/Dockerfile`

**Herramientas**
- [ ] `.pre-commit-config.yaml` (black, ruff, prettier, eslint, tests unitarios rápidos)

**Documentación**
- [ ] `docs/setup/dev.md`

### Checks de verificación

```bash
# Todo arranca sin errores
docker compose up --build

# API responde
curl http://localhost:8000/health   # → {"status":"ok"}

# Frontend accesible (pantalla "en construcción")
# abrir http://localhost:5173

# Tests pasan
make test

# Migraciones configuradas (vacías por ahora)
make migrate

# Auditoría de seguridad de dependencias (sin high/critical)
docker compose run --rm backend pip-audit
docker compose run --rm frontend npm audit
```

---

## Fase 1 — Autenticación y gestión de usuarios

**Objetivo:** login con email + contraseña, JWT con `token_version`, MFA TOTP obligatorio,
invalidación inmediata de sesión, CRUD de usuarios con bloqueo en lugar de eliminación.

**Estado:** `pendiente` _(no empezar hasta que Fase 0 esté completada y revisada)_

### Funcionalidades
- Login (email + contraseña) → access token + refresh token rotativo
- Flujo de activación MFA TOTP en el primer login (QR, verificación del código)
- Middleware de autenticación JWT con validación de `token_version`
- Endpoints protegidos con RBAC (admin / asesor)
- CRUD de usuarios: crear, editar, bloquear (`activo = false`), listar
- Invalidación inmediata: bloquear usuario incrementa `token_version`

### Ficheros principales a crear _(se detallará antes de implementar)_
- Modelo `Usuario` + migración Alembic
- `backend/app/core/security.py` (hash bcrypt, JWT, TOTP)
- `backend/app/api/auth.py` (login, refresh, mfa/setup, mfa/verify)
- `backend/app/api/usuarios.py`
- `backend/app/services/auth_service.py`
- Tests de integración: login, MFA, bloqueo, RBAC

---

## Fase 2 — Clientes, empresas y catálogo de modelos

**Objetivo:** CRUD de clientes y empresas, reasignación entre asesores, catálogo de modelos
fiscales (manual + origen aeat, sin ICS), vencimientos por periodo.

**Estado:** `pendiente`

### Funcionalidades
- CRUD de clientes (persona/entidad titular) con baja lógica
- CRUD de empresas (una o varias por cliente)
- Reasignación de cliente entre asesores (histórico incluido)
- Catálogo de modelos fiscales: alta, edición, desactivación
- `VencimientoModelo`: gestión de fechas límite por periodo (formato canónico estricto)
- Importación inicial CSV/Excel con informe de errores

---

## Fase 3 — Obligaciones fiscales y declaraciones

**Objetivo:** asignación de obligaciones a empresas, subida del justificante PDF, flujo "sin
actividad", gestión de anexos, cálculo y recálculo de estados.

**Estado:** `pendiente`

### Funcionalidades
- CRUD de obligaciones fiscales (empresa + modelo)
- Subida del justificante PDF (flujo principal)
- Flujo "sin actividad" (un clic, sin fichero)
- Gestión de anexos: subida múltiple, descarga con permisos, borrado
- Cálculo de estado en tiempo real al crear/modificar una declaración
- Job diario APScheduler (transición `pendiente → incumplido`)

---

## Fase 4 — Vistas, filtros y dashboard

**Objetivo:** vista global con filtros, vista por cliente/empresa, dashboard del asesor.

**Estado:** `pendiente`

### Funcionalidades
- Vista global: tabla con filtros (cliente, asesor, modelo, periodo, estado)
- Vista por defecto: mis clientes + periodo actual
- Vista por cliente/empresa con histórico de declaraciones
- Dashboard del asesor: próximos vencimientos, pendientes, incumplimientos
- Frontend completo (React + Tailwind, mobile-first)

---

## Fuera del MVP (Fase 2+ del producto)

Ver [SPEC.md — sección 8](../SPEC.md#8-plan-de-desarrollo-por-fases) para el detalle.

- Portal cliente con login propio + MFA
- MFA por SMS y email
- Sincronización ICS de la AEAT + vista de revisión del admin
- Dashboard del administrador con indicadores globales
- Notificaciones por email (vencimientos)
- Subida en bloque desde la vista tabla
