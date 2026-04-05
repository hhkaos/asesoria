# CLAUDE.md — Contexto del Proyecto: Plataforma de Control de Declaraciones Fiscales

Este fichero persiste el contexto del proyecto entre sesiones. Léelo siempre al inicio de una nueva conversación antes de hacer cualquier cambio.

---

## Qué es este proyecto

Aplicación web para un **despacho de asesoría fiscal** que controla el grado de cumplimiento de las declaraciones fiscales presentadas ante la AEAT.

**NO confecciona ni rellena declaraciones.** El flujo principal es:

1. El asesor descarga el justificante PDF de la sede electrónica de la AEAT.
2. Lo sube en la app, asignándolo a empresa + modelo + periodo.
3. La app registra la presentación y actualiza el estado de cumplimiento.

Existe también un flujo alternativo: marcar una obligación como **sin actividad** (declaración negativa o exenta) con un solo clic, sin necesidad de adjuntar fichero.

La especificación completa está en [SPEC.md](./SPEC.md). Léela si necesitas más detalle.

---

## Stack tecnológico

| Capa | Tecnología |
| --- | --- |
| Frontend | TypeScript + React (Vite) |
| Backend | Python 3.12 + FastAPI |
| Base de datos | PostgreSQL |
| ORM | SQLAlchemy (async) + Alembic (migraciones) |
| Autenticación | JWT (access + refresh tokens + `token_version`) + MFA (pyotp para TOTP; SMS y email OTP en Fase 2) |
| Tareas periódicas | APScheduler (job diario de estados, sincronización ICS AEAT, alertas) |
| Almacenamiento ficheros | Sistema de ficheros del VPS (`FILES_BASE_PATH` configurable) |
| Email | SMTP externo configurable (Office 365 o similar) |
| Despliegue | Docker Compose en VPS propio |
| Base de datos tests | PostgreSQL separada para tests (nunca mocks de BD) |

---

## Estructura de directorios (objetivo)

```text
asesoria/
├── backend/
│   ├── app/
│   │   ├── api/          # Routers FastAPI (endpoints)
│   │   ├── core/         # Config, seguridad, dependencias
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── schemas/      # Schemas Pydantic (request/response)
│   │   ├── services/     # Lógica de negocio
│   │   └── tasks/        # Tareas periódicas (APScheduler)
│   ├── tests/
│   │   ├── unit/         # Tests unitarios (lógica de negocio pura)
│   │   └── integration/  # Tests de endpoints con BD real
│   ├── alembic/          # Migraciones de BD
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # Cliente API (react-query + axios/fetch)
│   │   ├── components/   # Componentes reutilizables
│   │   ├── pages/        # Páginas / vistas
│   │   ├── hooks/        # Custom hooks
│   │   └── types/        # Tipos TypeScript
│   ├── package.json
│   └── Dockerfile
├── docs/                 # Documentación técnica (ver sección Documentación)
├── docker-compose.yml
├── .env.example
├── SPEC.md
└── CLAUDE.md
```

---

## Modelo de datos (resumen)

```text
Usuario (admin | asesor | cliente)
    │
    ├── Cliente (persona física/jurídica titular)
    │       │
    │       └── Empresa (NIF propio, una o varias por cliente)
    │               │
    │               └── ObligacionFiscal (empresa + modelo)
    │                       │
    │                       └── DeclaraciónPresentada (por periodo)
    │                               │
    │                               └── Anexo (0..N ficheros de contexto)
    │
    └── ModeloFiscal (catálogo: 303, 111, 190... o modelos manuales)
            │
            └── VencimientoModelo (fecha límite por periodo, versionado)
```

**Reglas clave:**

- Las obligaciones pertenecen a la **Empresa**, no al Cliente titular.
- Las fechas de vencimiento se guardan **por periodo** en `VencimientoModelo` — cambiar una fecha no altera el histórico.
- El justificante AEAT es el PDF principal; los **Anexos** son contexto adicional (aplazamientos, cálculos, complementarias...). No se muestran al cliente.
- `notas` en la declaración es texto libre **solo interno del despacho** — no visible para el cliente.
- **Declaraciones complementarias/sustitutivas** se gestionan como anexos de la declaración original.
- El `estado` se actualiza por **job diario** y también en tiempo real al crear/modificar una declaración.

**Formato canónico de periodos** (selectores en frontend, nunca texto libre):

| Periodicidad | Formato | Ejemplo |
| --- | --- | --- |
| Anual | `YYYY` | `2024` |
| Trimestral | `YYYY-TN` | `2024-T1` |
| Mensual | `YYYY-MM` | `2024-03` |

---

## Roles y permisos

| Acción | Admin | Asesor (propios clientes) | Asesor (clientes de compañero) | Cliente |
| --- | --- | --- | --- | --- |
| Ver todas las declaraciones | ✅ | ✅ | ✅ (lectura) | ❌ |
| Subir fichero / modificar declaración | ✅ | ✅ | ❌ | ❌ |
| Dar de alta clientes/empresas | ✅ | ✅ | ❌ | ❌ |
| Ver sus propias declaraciones | ✅ | ✅ | ✅ | ✅ |
| Gestionar catálogo modelos fiscales | ✅ | ❌ | ❌ | ❌ |
| Gestionar usuarios | ✅ | ❌ | ❌ | ❌ |
| Reasignar clientes entre asesores | ✅ | ❌ | ❌ | ❌ |
| Confirmar modelos ICS AEAT | ✅ | ❌ | ❌ | ❌ |

**Reglas de usuarios:**

- Los asesores **no se eliminan**, solo se bloquean (`activo = false`). El histórico conserva la autoría original.
- La **reasignación de clientes** aplica a todo (histórico incluido): el nuevo asesor queda como responsable.

---

## Autenticación y MFA

- **MFA obligatorio para los tres roles** (admin, asesor y cliente) desde el primer acceso. El mecanismo es idéntico para todos.
- Fase 1: solo TOTP (Google Authenticator, Authy). Fase 2: añadir SMS y email OTP.
- Tokens JWT: access token (corta duración) + refresh token rotativo.
- **Invalidación inmediata de sesión**: el campo `token_version` en el usuario se incrementa al bloquearlo; todos sus tokens previos son rechazados en el siguiente request.
- Los ficheros **no son accesibles por URL directa**: se sirven a través de la API con validación de permisos.

---

## Estados de cumplimiento

| Estado | Condición |
| --- | --- |
| `pendiente` | Dentro de plazo, sin declaración registrada |
| `presentado` | PDF subido o marcado sin_actividad, fecha ≤ fecha límite |
| `presentado_fuera_plazo` | PDF subido, fecha presentación > fecha límite |
| `sin_actividad` | Marcado negativa/exenta (con o sin fichero), dentro de plazo |
| `incumplido` | Plazo vencido sin ningún registro |

---

## Job diario de estados (APScheduler)

Se ejecuta una vez al día (hora configurable) y:

1. Compara la fecha actual con `VencimientoModelo.fecha_limite` para cada obligación activa y periodo vigente.
2. Actualiza el campo `estado` en `DeclaraciónPresentada` (cubre la transición automática `pendiente → incumplido`).
3. Genera la lista de incumplimientos nuevos para notificaciones.

El estado también se recalcula **en tiempo real** al crear o modificar una declaración (sin esperar al job).

---

## Estrategia de tests

**Filosofía:** tests en aspectos críticos, sin regresiones. Si algo que funcionaba se rompe, se añade el test antes de mergear el fix. Sin obsesión con % de cobertura.

**Prioridad:**

1. **Integración de API** (`pytest` + `httpx` + BD PostgreSQL real): endpoints reales, permisos RBAC, flujos de negocio completos.
2. **Unitarios backend** (`pytest`): funciones puras (cálculo de estados, formato de periodos, validaciones).
3. **Componentes frontend** (`Vitest`): hooks y componentes con lógica.
4. **E2E** (`Playwright`): diferido a fases posteriores.

**Ejecución:**

- **Pre-commit hook** (`pre-commit`): tests rápidos antes de cada commit.
- Suite completa: `make test`.

**Convenciones:**

- BD de test separada, nunca mocks de BD.
- Fixtures con estado conocido por test (`pytest` + `factory_boy` o similar).
- Tests en `backend/tests/unit/` y `backend/tests/integration/`.

---

## Fase 1 — MVP (alcance actual)

- [ ] Estructura base del proyecto (monorepo, Docker Compose, pre-commit)
- [ ] Autenticación: login, JWT con `token_version`, MFA TOTP, invalidación inmediata de sesión
- [ ] CRUD de usuarios (bloqueo en lugar de eliminación)
- [ ] CRUD de clientes y empresas; reasignación de clientes entre asesores
- [ ] Catálogo de modelos fiscales (manual + origen aeat; sin ICS en esta fase)
- [ ] Asignación de obligaciones fiscales a empresas
- [ ] Vencimientos por periodo con formato canónico estricto
- [ ] Subida del justificante PDF + flujo "sin actividad" (sin fichero, un clic)
- [ ] Gestión de anexos (subida múltiple, descarga, borrado)
- [ ] Job diario de actualización de estados + recálculo en tiempo real
- [ ] Vista global con filtros; vista por defecto = mis clientes + periodo actual
- [ ] Dashboard básico del asesor
- [ ] Importación inicial CSV/Excel con informe de errores
- [ ] Pre-commit hooks con tests críticos
- [ ] `docs/setup/dev.md` actualizado y verificado

**Fuera del MVP (Fase 2+):**

- Portal cliente (acceso con login propio + MFA)
- MFA por SMS y por email
- Sincronización ICS de la AEAT + vista de revisión del admin
- Dashboard del administrador con indicadores globales
- Notificaciones por email (vencimientos)
- Subida en bloque desde la vista tabla (picos de fin de trimestre)

---

## Decisiones de arquitectura tomadas

- **`tenant_id` en tablas principales** desde el inicio para migración futura a multi-tenant sin reescritura.
- **Ficheros en sistema de ficheros del VPS**: ruta base `FILES_BASE_PATH`. Límite por fichero configurable con `MAX_UPLOAD_SIZE_MB`.
- **APScheduler** en lugar de Celery+Redis: menos dependencias en el MVP (un solo proceso, sin broker).
- **Alembic** para todas las migraciones: nunca modificar la BD directamente.
- **Sin auditoría completa en Fase 1**: solo `subido_por` y `subido_en` en declaraciones y anexos.
- **Retención de datos indefinida**: solo el admin puede eliminar registros manualmente. Sin borrado automático.
- **Flujo de trabajo diario del asesor** (dashboard vs. vista global): pendiente de validar con el equipo antes de cerrar el diseño de UI.

---

## Variables de entorno (documentar en `.env.example`)

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/asesoria
DATABASE_TEST_URL=postgresql+asyncpg://user:pass@localhost:5432/asesoria_test
SECRET_KEY=...                  # Para firmar JWT
FILES_BASE_PATH=./data/files
MAX_UPLOAD_SIZE_MB=10           # Configurable
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
JOB_ESTADOS_HORA=02:00          # Hora de ejecución del job diario
```

---

## Entornos y despliegue

El sistema tiene tres entornos, cada uno con BD, ficheros y variables de entorno propias e independientes.

| Entorno | Propósito | Rama git |
| --- | --- | --- |
| `dev` | Desarrollo local de cada desarrollador | cualquier rama de feature |
| `staging` | Validación con el cliente antes de subir a prod | `main` o rama `release/*` |
| `prod` | Sistema en uso real del despacho | tags `vX.Y.Z` |

**Regla de promoción:** dev → staging → prod. Nunca se despliega directamente a prod sin pasar por staging.

### Gestión de migraciones entre entornos

- **Nunca se modifica la BD manualmente** en ningún entorno.
- Al desplegar en cualquier entorno: `alembic upgrade head` antes de arrancar la aplicación.
- Las migraciones deben ser reversibles siempre que sea posible (`downgrade`).
- En staging y prod, hacer **backup de la BD antes** de aplicar migraciones.

### Ficheros `.env` por entorno

Cada entorno tiene su propio fichero `.env`, que nunca se sube al repositorio.

```text
.env.example    ← en el repo, con todas las variables documentadas y sin valores reales
.env            ← local (dev), en .gitignore
                   en staging/prod: gestionado manualmente en el servidor
```

---

## Documentación del proyecto

Toda la documentación técnica vive en `docs/` dentro del repositorio y se mantiene actualizada con el código.

### Estructura de `docs/`

```text
docs/
├── setup/
│   ├── dev.md          # Montar el entorno local desde cero
│   ├── staging.md      # Instalar y configurar el entorno de staging
│   └── prod.md         # Instalar y configurar producción
├── deployment/
│   ├── promotion.md    # Checklist paso a paso: dev → staging → prod
│   ├── migrations.md   # Gestión de migraciones de BD en cada entorno
│   └── rollback.md     # Cómo revertir un despliegue fallido
├── architecture/
│   └── decisions.md    # Registro de decisiones de arquitectura (ADRs)
└── api/
    └── README.md       # Referencia de la API (complementa el /docs de FastAPI)
```

### Contenido mínimo de cada documento

**`docs/setup/dev.md`:** requisitos previos (Docker, Python, Node), clonar el repo, configurar `.env`, arrancar con `docker compose up`, ejecutar migraciones, cargar datos de ejemplo, ejecutar los tests.

**`docs/setup/staging.md` y `prod.md`:** requisitos del servidor (SO, puertos, DNS), instalación de Docker en el VPS, configuración del `.env`, configuración de HTTPS (Let's Encrypt / Certbot), arranque inicial y verificación.

**`docs/deployment/promotion.md`:** checklist de pasos para cada promoción, backup de BD, aplicación de migraciones, verificación post-despliegue, comunicación al cliente.

**`docs/deployment/rollback.md`:** cómo revertir la aplicación a la versión anterior, cómo revertir una migración (`alembic downgrade`), criterios para decidir hacer rollback.

### Cuándo actualizar la documentación

- Nueva variable de entorno → actualizar `.env.example` y el doc de setup correspondiente.
- Nueva migración de BD → verificar que `promotion.md` sigue siendo válido.
- Cambio en el proceso de despliegue → actualizar `promotion.md` antes de mergear.
- La documentación se revisa como parte del checklist de cada entrega al cliente.

---

## UI — Responsive / mobile-first

La interfaz debe funcionar correctamente en móvil, tablet y escritorio. El diseño parte de **mobile-first** y escala progresivamente.

- Usar Tailwind CSS (o similar) con breakpoints estándar: `sm` (640px), `md` (768px), `lg` (1024px).
- Los flujos críticos (subir fichero, marcar sin actividad, consultar estado) deben ser usables en pantalla de móvil sin scroll horizontal.
- Las tablas con muchas columnas deben adaptarse en móvil (columnas colapsables, scroll horizontal contenido, o vista de tarjetas).
- Los modales, formularios y acciones de confirmación deben estar optimizados para interacción táctil (tamaño mínimo de área táctil).

---

## Convenciones de código

- Python: `black` + `ruff` (formato y linting). `mypy` en módulos de lógica de negocio.
- TypeScript: `eslint` + `prettier`.
- Commits descriptivos. Nunca commitear `.env` ni secretos.
