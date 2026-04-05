# Especificación Funcional
## Plataforma Web para Control de Declaraciones Fiscales Presentadas

> Versión 0.3 — Resultado de sesiones de discovery y revisión en profundidad

---

## 1. Objetivo

Desarrollar una aplicación web para un despacho de asesoría fiscal que permita **controlar y hacer seguimiento del grado de cumplimiento de las declaraciones fiscales presentadas** ante la AEAT.

**El sistema NO confecciona ni rellena declaraciones.** Su función es:
- Registrar qué obligaciones fiscales tiene cada cliente/empresa.
- Que el asesor suba el fichero PDF descargado de la sede electrónica de la AEAT como evidencia de presentación.
- Mostrar el estado de cumplimiento (presentado, pendiente, fuera de plazo, incumplido).
- Permitir filtrar y visualizar el estado por cliente, por asesor y por modelo fiscal.

---

## 2. Alcance y Contexto

| Parámetro | Valor |
|---|---|
| Tipo de sistema | Single-tenant (un despacho), arquitectura preparada para multi-tenant futuro |
| Usuarios (asesores) | 6–20 |
| Clientes (personas/empresas) | 500–2.000 |
| Infraestructura | VPS propio |
| Frontend | TypeScript + React (Vite) |
| Backend | Python + FastAPI |
| Base de datos | PostgreSQL |
| Almacenamiento ficheros | Sistema de ficheros del VPS (ruta configurable) |
| Metodología | Ágil e iterativa — MVP validado conjuntamente, fases incrementales |

---

## 3. Roles y Permisos

### 3.1 Administrador
- Acceso completo a todo el sistema.
- Alta/baja/modificación de usuarios. Los asesores no se eliminan, solo se bloquea su acceso (ver sección 5.1).
- Reasignación de clientes entre asesores (incluyendo histórico).
- Configuración global: modelos fiscales, calendario AEAT, parámetros del sistema.
- Revisión y confirmación de nuevos modelos detectados en el calendario AEAT.

### 3.2 Asesor / Empleado
- Puede dar de alta clientes y empresas.
- Gestiona las obligaciones y declaraciones de los clientes que tiene asignados.
- **Puede visualizar** todos los clientes y el estado de cumplimiento de sus compañeros (lectura global).
- **No puede subir ni modificar** ficheros ni estados de clientes asignados a otro asesor.

### 3.3 Cliente (portal — Fase 2)

- Accede con email + contraseña + **MFA obligatorio** (mismo mecanismo que admin y asesor).
- Solo puede ver sus propias entidades (la persona física/jurídica y las empresas asociadas a ella).
- No puede ver clientes ni datos de otros.
- Las notas internas de las declaraciones **no son visibles** para el cliente.

---

## 4. Modelo de Datos

### 4.1 Cliente (Persona o Entidad Titular)
Representa a la persona física o jurídica titular de la relación con el despacho.

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| nombre | string | Nombre completo o razón social |
| nif | string | NIF/CIF del titular |
| tipo | enum | autónomo, empresa, particular, etc. |
| email_acceso | string | Email para acceso al portal cliente (Fase 2) |
| asesor_id | FK | Asesor/empleado responsable actual |
| activo | bool | Alta/baja lógica |

### 4.2 Empresa / Entidad Fiscal
Una o varias empresas asociadas a un Cliente titular. Las obligaciones fiscales van siempre ligadas a una Empresa.

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| cliente_id | FK | Titular al que pertenece |
| nombre | string | Razón social |
| nif | string | NIF/CIF de la empresa |
| tipo | enum | S.L., S.A., autónomo, comunidad de bienes, etc. |

### 4.3 Modelo Fiscal
Catálogo de modelos fiscales. Pueden ser modelos oficiales de la AEAT (importados del calendario ICS) o modelos personalizados creados manualmente por el administrador o asesor (recurrentes no publicados por la AEAT).

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| codigo | string | Identificador (ej. "303", o código libre para modelos propios) |
| nombre | string | Nombre descriptivo (ej. "IVA trimestral") |
| subtitulo | string | Descripción adicional |
| periodicidad | enum | mensual, trimestral, anual, esporádico |
| origen | enum | aeat, manual |
| activo | bool | Si se usa actualmente |

### 4.4 Vencimiento de Modelo (histórico)
Permite cambiar la fecha límite de un modelo para un periodo concreto sin alterar el histórico de presentaciones ya registradas.

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| modelo_id | FK | Modelo fiscal |
| periodo | string | Formato canónico según periodicidad (ver sección 4.9) |
| fecha_limite | date | Fecha límite de presentación para ese periodo |
| origen | enum | manual, importado_ics_aeat |

### 4.5 Obligación Fiscal
Relación entre una Empresa y un Modelo Fiscal: qué declaraciones debe presentar esa empresa.

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| empresa_id | FK | Empresa obligada |
| modelo_id | FK | Modelo fiscal |
| activa | bool | Si la obligación sigue vigente |
| fecha_inicio | date | Desde cuándo aplica |
| fecha_fin | date | Hasta cuándo aplica (null = indefinido) |

### 4.6 Declaración Presentada
Registro de una presentación concreta: evidencia de que una obligación ha sido cumplida en un periodo concreto. Puede tener cero o más anexos (ver 4.7).

El **estado** se calcula dinámicamente mediante un job diario (ver sección 5.7) en función de la fecha de presentación, la fecha límite del periodo y si existe fichero o marcado de sin actividad.

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| obligacion_id | FK | Obligación fiscal |
| periodo | string | Formato canónico según periodicidad (ver sección 4.9) |
| fecha_presentacion | date | Fecha real de presentación (null si sin_actividad sin fichero) |
| numero_justificante | string | Número de justificante AEAT (null si sin_actividad) |
| resultado | enum | a_ingresar, a_devolver, sin_actividad, negativa |
| importe | decimal | Importe (positivo = a ingresar, negativo = a devolver; null si no aplica) |
| estado | enum | pendiente, presentado, presentado_fuera_plazo, sin_actividad, incumplido |
| fichero_path | string | Ruta del PDF justificante AEAT (null si sin_actividad sin fichero) |
| fichero_nombre | string | Nombre original del fichero justificante |
| notas | text | Notas internas del asesor. **No visibles para el cliente.** |
| subido_por | FK | Usuario que creó el registro |
| subido_en | datetime | Fecha/hora de creación del registro |

### 4.7 Anexo de Declaración
Documentos adicionales adjuntos a una declaración presentada. Sirven como contexto de trabajo para el asesor: bases de cálculo, aplazamientos, declaraciones complementarias, requerimientos, capturas, etc. **No se muestran al cliente en el portal.**

Dado que las declaraciones complementarias o sustitutivas también se gestionan mediante anexos, pueden adjuntarse múltiples ficheros del mismo tipo a una misma declaración.

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| declaracion_id | FK | Declaración presentada a la que pertenece |
| nombre | string | Nombre descriptivo del anexo |
| fichero_path | string | Ruta del fichero en el servidor |
| fichero_nombre | string | Nombre original del fichero |
| tipo_mime | string | Tipo MIME del fichero |
| subido_por | FK | Usuario que subió el anexo |
| subido_en | datetime | Fecha/hora de subida |

**Formatos admitidos para anexos:** PDF, Excel (.xlsx, .xls), imágenes (JPG, PNG, WEBP), y cualquier otro documento de contexto relevante.

### 4.8 Usuario del Sistema

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| nombre | string | Nombre completo |
| email | string | Email de acceso |
| rol | enum | admin, asesor, cliente |
| activo | bool | Si puede iniciar sesión (false = bloqueado, no eliminado) |
| token_version | int | Se incrementa para invalidar todos los tokens activos inmediatamente |
| mfa_activo | bool | MFA habilitado |
| mfa_metodo | enum | totp, sms, email |
| mfa_secreto | string | Secreto cifrado (TOTP) o teléfono (SMS) |

### 4.9 Formato Canónico de Periodos

El campo `periodo` siempre sigue un formato estricto según la periodicidad del modelo. El frontend usa selectores, nunca texto libre.

| Periodicidad | Formato | Ejemplo |
|---|---|---|
| Anual | `YYYY` | `2024` |
| Trimestral | `YYYY-TN` | `2024-T1`, `2024-T4` |
| Mensual | `YYYY-MM` | `2024-01`, `2024-12` |
| Esporádico | `YYYY` o definido manualmente | `2024` |

---

## 5. Funcionalidades

### 5.1 Autenticación y Gestión de Sesiones

- Login con email + contraseña.
- **MFA obligatorio para todos los roles** (admin, asesor y cliente) desde el primer acceso. El mecanismo es idéntico independientemente del rol.
- El usuario elige su método de segundo factor:
  - **TOTP** (Google Authenticator, Authy): escaneo de QR, códigos de 6 dígitos. *(Fase 1)*
  - **SMS**: código enviado al móvil (requiere proveedor tipo Twilio). *(Fase 2)*
  - **Email**: código OTP enviado al correo. *(Fase 2)*
- Flujo de activación de MFA guiado en el primer login (válido para cualquier rol).
- Recuperación de acceso si se pierde el segundo factor: solo vía administrador.
- **Invalidación inmediata de sesión**: cuando el admin bloquea un usuario, todos sus tokens activos se invalidan en el acto mediante el campo `token_version`. No hay ventana de gracia.
- Los asesores **no se eliminan** del sistema; se bloquea su acceso (`activo = false`). El histórico de declaraciones que subieron permanece intacto con su autoría.

---

### 5.2 Gestión de Clientes y Empresas

- Alta, edición y baja lógica de clientes (persona/entidad titular).
- Cada cliente puede tener una o varias empresas/entidades fiscales asociadas.
- Asignación del asesor responsable.
- **Reasignación de clientes**: el admin puede transferir uno o varios clientes de un asesor a otro. La reasignación aplica a todo, incluyendo el histórico de declaraciones, que queda vinculado al nuevo asesor responsable.
- **Importación inicial masiva** mediante Excel/CSV con clientes, empresas y sus obligaciones fiscales.
  - Formato a definir con cabeceras documentadas.
  - Validación previa antes de importar con informe detallado de errores (NIF inválido, duplicados, modelo desconocido, etc.).

---

### 5.3 Catálogo de Modelos Fiscales

El administrador y los asesores pueden gestionar el catálogo de modelos.

- Alta, edición y desactivación de modelos.
- Campos por modelo: código, nombre, subtítulo, periodicidad, origen (aeat | manual).
- Los **modelos manuales** permiten registrar obligaciones recurrentes propias del despacho no publicadas por la AEAT (ej. modelos autonómicos, liquidaciones internas, etc.).
- Las fechas límite se gestionan por periodo en `VencimientoModelo` (sección 4.4): cambiar una fecha límite no altera el histórico.

#### Integración con Calendario ICS de la AEAT
- El sistema consume periódicamente los calendarios ICS publicados por la AEAT:
  - URL de referencia: `https://sede.agenciatributaria.gob.es/Sede/ayuda/calendario-contribuyente/icalendar/instrucciones-integrar-calendario.html`
- La **periodicidad de sincronización es configurable** por el administrador.
- Cuando se detectan nuevos eventos (modelos/periodos no existentes en el sistema), se genera una **vista de revisión** para el administrador.
- El administrador revisa los nuevos modelos detectados y decide cuáles dar de alta.
- **No se realizan cambios automáticos** sin confirmación del administrador.

---

### 5.4 Asignación de Obligaciones Fiscales

- El asesor asigna obligaciones fiscales a cada empresa del cliente, una a una.
- Se indica el modelo, desde qué periodo aplica y opcionalmente hasta cuándo.
- Las obligaciones pueden desactivarse (`fecha_fin`) sin eliminarse.
- El job diario (sección 5.7) usa las obligaciones activas para generar y mantener los registros de cumplimiento por periodo.

---

### 5.5 Subida de Ficheros AEAT (flujo principal)

**Flujo estándar (declaración con justificante):**

1. El asesor descarga el justificante/acuse de recibo en PDF desde la sede electrónica de la AEAT.
2. Entra en la obligación correspondiente (empresa + modelo + periodo) y sube el PDF.
3. Completa o confirma los campos: fecha de presentación, número de justificante, resultado, importe, y opcionalmente una nota interna de contexto.
4. El sistema registra la declaración y el job diario actualizará el estado; el cambio también es inmediato en la vista.

**Flujo sin actividad (declaración negativa o exenta):**

- El asesor marca la obligación como `sin_actividad` con un solo clic, sin necesidad de adjuntar fichero.
- La AEAT no siempre genera justificante para declaraciones negativas o exenciones; este flujo lo contempla.

**Reglas comunes:**

- Se puede reemplazar el fichero justificante subido por error.
- La extracción automática de datos del PDF (NIF, modelo, periodo) queda **diferida a Fase 3**.
- Las **declaraciones complementarias o sustitutivas** se gestionan adjuntando el nuevo fichero como anexo de la declaración original, pudiendo añadirse múltiples anexos del mismo tipo.

---

### 5.6 Anexos de una Declaración

Cada declaración puede tener cero o más anexos. Su propósito es conservar el **contexto de trabajo** del asesor para poder responder preguntas futuras sobre el impuesto presentado (aplazamientos, bases de cálculo, requerimientos, etc.). Son de uso **interno del despacho** y no se muestran al cliente.

**Qué se puede adjuntar:**

- Ficheros PDF (aplazamiento, requerimiento, respuesta a la AEAT, complementaria...)
- Hojas de cálculo Excel/CSV (bases imponibles, cálculos previos, liquidaciones...)
- Imágenes (JPG, PNG, WEBP) — capturas de pantalla, justificantes escaneados...
- Cualquier otro documento de contexto relevante

**Funcionalidades:**

- Añadir nuevos anexos en cualquier momento posterior a la creación de la declaración.
- Asignar un nombre descriptivo a cada anexo al subirlo.
- Visualizar la lista de anexos desde la ficha de la declaración.
- Descargar cualquier anexo individualmente.
- Eliminar un anexo (solo el asesor que lo subió o el administrador).
- Los anexos se sirven a través de la API con validación de permisos (no accesibles por URL directa).
- **Límite de tamaño por fichero**: configurable por variable de entorno (`MAX_UPLOAD_SIZE_MB`).

---

### 5.7 Estados de Cumplimiento y Job Diario

#### Estados posibles

Por cada obligación en un periodo concreto:

| Estado | Condición |
|---|---|
| `pendiente` | Dentro de plazo, sin declaración registrada |
| `presentado` | PDF subido o marcado sin_actividad, fecha ≤ fecha límite |
| `presentado_fuera_plazo` | PDF subido, fecha presentación > fecha límite |
| `sin_actividad` | Marcado como negativa/exenta (con o sin fichero), dentro de plazo |
| `incumplido` | Plazo vencido sin ningún registro |

#### Job diario de actualización de estados

Un proceso programado se ejecuta **una vez al día** (hora configurable) y realiza:

1. Para cada obligación activa y cada periodo vigente, verifica si existe declaración registrada.
2. Compara la fecha actual con la `fecha_limite` del `VencimientoModelo` correspondiente.
3. Actualiza el campo `estado` en `DeclaraciónPresentada` según las reglas anteriores.
4. Genera la lista de incumplimientos nuevos para las alertas de notificación.

**Nota:** el estado también se recalcula inmediatamente al crear o modificar una declaración, sin esperar al job nocturno. El job cubre los cambios de estado por paso del tiempo (pendiente → incumplido).

---

### 5.8 Vistas y Filtros

#### Vista global (todas las obligaciones del despacho)
- Tabla con todas las declaraciones/obligaciones.
- **Filtros disponibles:**
  - Por cliente o empresa (búsqueda por nombre/NIF)
  - Por asesor/empleado responsable
  - Por modelo fiscal (303, 111, 190...)
  - Por periodo/ejercicio (selector canónico)
  - Por estado de cumplimiento
- **Vista por defecto al entrar:** filtrada por "mis clientes asignados" + "periodo actual". Cada usuario ve inicialmente solo su carga de trabajo relevante.
- Acceso de lectura global para todos los asesores y admins.

#### Vista por cliente/empresa
- Ficha del cliente con sus empresas asociadas.
- Por empresa: listado de sus obligaciones y estado de cada periodo.
- Histórico de declaraciones con opción de descarga del justificante y los anexos.

#### Vista por asesor

- Listado de clientes asignados con % de cumplimiento global.
- Un asesor puede consultar la vista de sus compañeros (lectura).

---

### 5.9 Dashboard

Panel principal diferenciado por rol.

**Dashboard del asesor:**

- Próximos vencimientos de mis clientes (ventana configurable: próximos N días).
- Mis declaraciones pendientes de subir (obligaciones sin registro dentro de plazo).
- Mis incumplimientos (plazo vencido sin presentación).
- Resumen por modelo fiscal: cuántos presentados, cuántos pendientes, cuántos incumplidos.

> **Nota de diseño:** el flujo de trabajo diario exacto (si los asesores arrancan desde el dashboard o desde la vista global) debe validarse observando el proceso actual del despacho antes de finalizar el diseño de la UI.

**Dashboard del administrador** (además de lo anterior):
- Indicadores globales del despacho: % cumplimiento total, por asesor, por modelo.
- Alertas de nuevos modelos detectados en el calendario AEAT pendientes de revisión.

---

### 5.10 Notificaciones

- Avisos automáticos por email para vencimientos próximos sin presentar:
  - 7 días antes del vencimiento
  - 1 día antes
  - Día de vencimiento
- **Proveedor de email**: SMTP externo configurable (Office 365 o similar). Configuración por variables de entorno.
- No es crítico para el MVP; se activa en Fase 2.
- Notificaciones internas en la app (bandeja de avisos).

---

## 6. Arquitectura Técnica

### 6.1 Stack
| Capa | Tecnología |
|---|---|
| Frontend | TypeScript + React (Vite) |
| Backend API | Python + FastAPI |
| Base de datos | PostgreSQL |
| ORM | SQLAlchemy (async) + Alembic (migraciones) |
| Autenticación | JWT (access + refresh tokens con `token_version`) + MFA (pyotp para TOTP) |
| Almacenamiento | Sistema de ficheros del VPS (`FILES_BASE_PATH` configurable) |
| Tareas periódicas | APScheduler (job diario de estados + sincronización ICS) |
| Despliegue | Docker Compose en VPS |

### 6.2 Consideraciones de Diseño Multi-Tenant (futuro)

Aunque el sistema arranca como single-tenant:

- Campo `tenant_id` en las tablas principales desde el inicio.
- Configuración (SMTP, calendarios AEAT, parámetros) aislable a nivel de tenant.
- Subdominios o cabecera HTTP para identificar el tenant en versiones futuras.

### 6.3 Seguridad

- Contraseñas hasheadas con bcrypt.
- Secretos MFA cifrados en base de datos.
- HTTPS obligatorio en el VPS (Let's Encrypt).
- Tokens JWT de corta duración con refresh token rotativo.
- **Invalidación inmediata de sesión** mediante `token_version`: al bloquearse un usuario, todos sus tokens emitidos anteriormente son rechazados en el siguiente request.
- Control de acceso por rol en cada endpoint (RBAC).
- Los ficheros (justificantes y anexos) se sirven exclusivamente a través de la API con validación de permisos; no son accesibles por URL directa.
- Límite de tamaño de fichero configurable (`MAX_UPLOAD_SIZE_MB`).

---

## 7. Ideas y Extensiones Futuras

Funcionalidades fuera del roadmap actual pero de interés para versiones futuras.

### Bot conversacional (Telegram u otro canal)

Integración de un bot de mensajería (Telegram, WhatsApp Business, Slack...) que permita al asesor interactuar con el sistema en lenguaje natural sin abrir la aplicación web.

**Concepto:**
- El asesor envía un mensaje al bot: *"Marca el 303 del tercer trimestre de Empresa X como presentado"*.
- Un LLM interpreta la intención (intent), extrae las entidades relevantes (empresa, modelo, periodo, acción) y las resuelve contra los datos del sistema.
- Antes de ejecutar el cambio, el bot **muestra un resumen de la acción propuesta y solicita confirmación explícita** al asesor.
- Solo tras confirmar, el sistema aplica el cambio vía la API interna.

**Casos de uso previstos:**
- Actualizar el estado de una declaración o marcarla como presentada.
- Consultar el estado de cumplimiento de un cliente o empresa.
- Ver los vencimientos próximos del día o la semana.
- Recibir alertas proactivas de incumplimientos sin entrar en la app.

**Consideraciones técnicas:**
- El LLM actúa únicamente como capa de interpretación; toda la lógica de negocio y validaciones residen en el backend.
- La confirmación es obligatoria para cualquier acción de escritura — el bot nunca modifica datos sin aprobación explícita del asesor.
- La autenticación del usuario en el bot debe vincularse a su cuenta en el sistema (token de sesión o enlace de verificación).
- El historial de acciones realizadas vía bot queda registrado igual que las realizadas desde la web.

---

## 8. Plan de Desarrollo por Fases

### Fase 1 — MVP

- Autenticación con MFA (TOTP), invalidación inmediata de sesión.
- CRUD de usuarios (admin gestiona asesores; bloqueo, no eliminación).
- CRUD de clientes, empresas y obligaciones fiscales.
- Reasignación de clientes entre asesores (con histórico).
- Catálogo de modelos fiscales (manual + origen aeat, sin ICS en esta fase).
- Vencimientos por periodo con formato canónico estricto.
- Subida del justificante PDF y flujo de "sin actividad" (sin fichero).
- Gestión de anexos (subida múltiple, descarga, borrado).
- Job diario de actualización de estados.
- Vista global con filtros; vista por defecto = mis clientes + periodo actual.
- Dashboard básico del asesor.
- Importación inicial CSV/Excel de clientes con informe de errores.
- Pre-commit hooks con tests críticos.

### Fase 2
- Portal del cliente (acceso con email + MFA).
- Sincronización ICS de la AEAT + vista de revisión del admin.
- Dashboard del administrador con indicadores globales.
- MFA por SMS y por email (además de TOTP).
- Notificaciones por email (vencimientos).
- Subida en bloque desde la vista tabla (para picos de fin de trimestre).

### Fase 3
- Extracción automática de datos del PDF al subirlo.
- Exportación de informes (Excel/PDF).
- Multitenancy.
- Posibles integraciones con software contable.

---

## 8. Requisitos No Funcionales

| Requisito | Detalle |
|---|---|
| Escalabilidad | Hasta 2.000 clientes y decenas de miles de declaraciones anuales |
| Rendimiento | Listados y filtros con respuesta < 1 s para el volumen previsto |
| Seguridad | Datos fiscales sensibles: HTTPS, cifrado, RBAC, sin URLs directas a ficheros |
| Usabilidad | Interfaz orientada a revisión rápida; mínimo de clics para subir un fichero o marcar sin actividad |
| Responsive / mobile-first | La interfaz debe funcionar correctamente en móvil, tablet y escritorio. El diseño parte de mobile-first y se adapta progresivamente a pantallas más grandes. |
| Disponibilidad | VPS con backups periódicos de BD y ficheros |
| Trazabilidad | Cada declaración registra el usuario y la fecha/hora de creación |
| Multi-entorno | El sistema soporta tres entornos (dev, staging, prod) con configuración aislada y proceso documentado de promoción de cambios |
| Documentación | Toda instalación, configuración y proceso de despliegue debe estar documentado para que cualquier miembro del equipo pueda reproducirlo sin asistencia |

---

## 9. Supuestos y Decisiones

- El sistema NO confecciona ni presenta declaraciones: solo registra y controla las ya presentadas.
- La fuente de verdad son los ficheros PDF descargados de la sede electrónica de la AEAT.
- Un cliente (persona/entidad titular) puede tener varias empresas; las obligaciones son siempre por empresa.
- Las fechas de vencimiento se versionan por periodo para preservar el histórico ante cambios futuros.
- El estado de cumplimiento se calcula por job diario y también en tiempo real al crear/modificar una declaración.
- Las declaraciones complementarias o sustitutivas se gestionan como anexos de la declaración original.
- Las notas de las declaraciones son siempre internas del despacho (no visibles para el cliente).
- Los asesores no se eliminan: solo se bloquean. El histórico de sus acciones queda intacto.
- La política de retención de datos es conservar todo indefinidamente; solo el administrador puede eliminar registros manualmente.
- No se implementa auditoría completa en Fase 1.
- El MFA es obligatorio para todos los roles (admin, asesor y cliente) desde el primer acceso. El mecanismo es idéntico para los tres. (TOTP en Fase 1; SMS y email en Fase 2).
- El flujo de trabajo diario del asesor debe validarse con el equipo antes de finalizar el diseño del dashboard.

---

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| Variabilidad en formatos PDF de la AEAT | Parseo automático diferido a Fase 3; entrada manual en Fase 1 |
| Cambios en el formato del ICS de la AEAT | Capa de adaptación configurable; revisión manual antes de confirmar cambios |
| Pérdida de ficheros en el VPS | Backups periódicos automatizados; considerar MinIO en el futuro |
| Escalabilidad del VPS | Arquitectura dockerizada facilita migración a cloud si fuera necesario |
| Cumplimiento RGPD | Datos fiscales sensibles; política de conservación indefinida con borrado solo por admin; consultar asesoría legal para obligaciones formales de retención |
| Diseño del dashboard sin validar flujo real | Validar con los asesores cómo trabajan actualmente antes de cerrar el diseño de la UI |
