# Especificación Funcional
## Plataforma Web para Control de Declaraciones Fiscales Presentadas

> Versión 0.2 — Resultado de sesión de discovery con el cliente

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
| Frontend | TypeScript (React + framework a definir) |
| Backend | Python + FastAPI |
| Base de datos | PostgreSQL |
| Almacenamiento ficheros | Sistema de ficheros del VPS |
| Metodología | Ágil e iterativa — MVP validado conjuntamente, fases incrementales |

---

## 3. Roles y Permisos

### 3.1 Administrador
- Acceso completo a todo el sistema.
- Alta/baja/modificación de usuarios (asesores y clientes).
- Configuración global: modelos fiscales, calendario AEAT, parámetros del sistema.
- Revisión y confirmación de nuevos modelos detectados en el calendario AEAT.

### 3.2 Asesor / Empleado
- Puede dar de alta clientes y empresas.
- Gestiona las obligaciones de los clientes que tiene asignados.
- **Puede visualizar** todos los clientes y el estado de cumplimiento de sus compañeros (visibilidad global del despacho).
- **No puede subir ni modificar** ficheros ni estados de clientes asignados a otro asesor.

### 3.3 Cliente (portal)
- Accede con email + contraseña + MFA.
- Solo puede ver sus propias entidades (la persona física/jurídica y las empresas asociadas a ella).
- No puede ver clientes ni datos de otros.

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
| email_acceso | string | Email para acceso al portal cliente |
| asesor_id | FK | Asesor/empleado responsable |
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
Catálogo de modelos fiscales configurables por el administrador.

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| codigo | string | Identificador oficial (ej. "303") |
| nombre | string | Nombre descriptivo (ej. "IVA trimestral") |
| subtitulo | string | Descripción adicional |
| periodicidad | enum | mensual, trimestral, anual, esporádico |
| activo | bool | Si se usa actualmente |

### 4.4 Vencimiento de Modelo (histórico)
Permite cambiar la fecha límite de un modelo sin alterar el histórico de presentaciones.

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| modelo_id | FK | Modelo fiscal |
| periodo | string | Ej. "2024-T1", "2024-11" |
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
Registro de una presentación concreta: evidencia de que una obligación ha sido cumplida en un periodo. Puede tener cero o más anexos (ver 4.7).

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| obligacion_id | FK | Obligación fiscal |
| periodo | string | Ej. "2024-T1" |
| fecha_presentacion | date | Fecha real de presentación |
| numero_justificante | string | Número de justificante AEAT |
| resultado | enum | a_ingresar, a_devolver, sin_actividad, negativa |
| importe | decimal | Importe (positivo = a ingresar, negativo = a devolver) |
| estado | enum | Ver sección 5.6 |
| fichero_path | string | Ruta del PDF justificante AEAT en el servidor |
| fichero_nombre | string | Nombre original del fichero justificante |
| notas | text | Texto libre de contexto (descripción, observaciones, etc.) |
| subido_por | FK | Usuario que subió el fichero |
| subido_en | datetime | Fecha/hora de subida |

### 4.7 Anexo de Declaración
Documentos o archivos adicionales adjuntos a una declaración presentada. Sirven como contexto de trabajo para el asesor: bases de cálculo, aplazamientos, requerimientos, capturas, etc.

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| declaracion_id | FK | Declaración presentada a la que pertenece |
| nombre | string | Nombre descriptivo del anexo |
| fichero_path | string | Ruta del fichero en el servidor |
| fichero_nombre | string | Nombre original del fichero |
| tipo_mime | string | Tipo MIME del fichero (PDF, Excel, imagen, etc.) |
| subido_por | FK | Usuario que subió el anexo |
| subido_en | datetime | Fecha/hora de subida |

**Formatos admitidos para anexos:** PDF, Excel (.xlsx, .xls), imágenes (JPG, PNG, WEBP), y cualquier otro fichero relevante.

---

### 4.8 Usuario del Sistema

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID | Clave primaria |
| nombre | string | Nombre completo |
| email | string | Email de acceso |
| rol | enum | admin, asesor, cliente |
| mfa_activo | bool | MFA habilitado |
| mfa_metodo | enum | totp, sms, email |
| mfa_secreto | string | Secreto cifrado (TOTP) o teléfono (SMS) |

---

## 5. Funcionalidades

### 5.1 Autenticación y MFA

- Login con email + contraseña.
- **MFA obligatorio para todos los usuarios** en el primer acceso.
- El usuario elige su método de segundo factor:
  - **TOTP** (Google Authenticator, Authy): escaneo de QR, códigos de 6 dígitos.
  - **SMS**: código enviado al móvil (requiere proveedor tipo Twilio).
  - **Email**: código OTP enviado al correo.
- Flujo de activación de MFA guiado en el primer login.
- Recuperación de acceso si se pierde el segundo factor (solo vía admin).

---

### 5.2 Gestión de Clientes y Empresas

- Alta, edición y baja lógica de clientes (persona/entidad titular).
- Cada cliente puede tener una o varias empresas/entidades fiscales asociadas.
- Asignación del asesor responsable.
- **Importación inicial masiva** mediante Excel/CSV con clientes, empresas y sus obligaciones fiscales.
  - Formato a definir con cabeceras documentadas.
  - Validación previa antes de importar (errores de NIF, duplicados, etc.).

---

### 5.3 Catálogo de Modelos Fiscales

- El administrador gestiona el catálogo de modelos disponibles (alta, edición, desactivación).
- Campos por modelo: código, nombre, subtítulo, periodicidad.
- Las fechas límite se gestionan por periodo (ver sección 4.4), de modo que un cambio de fecha no altera el histórico.

#### Integración con Calendario ICS de la AEAT
- El sistema consume periódicamente los calendarios ICS publicados por la AEAT:
  - URL de referencia: `https://sede.agenciatributaria.gob.es/Sede/ayuda/calendario-contribuyente/icalendar/instrucciones-integrar-calendario.html`
- La **periodicidad de sincronización es configurable** por el administrador.
- Cuando se detectan nuevos eventos (modelos/periodos no existentes en el sistema), se genera una **vista de revisión** para el administrador.
- El administrador revisa los nuevos modelos detectados y decide cuáles dar de alta en el catálogo.
- No se realizan cambios automáticos sin confirmación del administrador.

---

### 5.4 Asignación de Obligaciones Fiscales

- El asesor asigna obligaciones fiscales a cada empresa del cliente, una a una.
- Se indica el modelo y desde qué periodo aplica.
- Las obligaciones pueden desactivarse (fecha_fin) sin eliminarse.

---

### 5.5 Subida de Ficheros AEAT (flujo principal)

1. El asesor descarga el justificante/acuse de recibo en PDF desde la sede electrónica de la AEAT.
2. Entra en la obligación correspondiente (empresa + modelo + periodo) y sube el PDF.
3. Completa o confirma los campos: fecha de presentación, número de justificante, resultado, importe, y opcionalmente una nota de contexto.
4. El sistema registra la declaración como **Presentada** y actualiza el indicador de cumplimiento.
5. Opcionalmente, el asesor puede adjuntar uno o más **anexos** a la declaración (ver sección 5.6).

- **Formato del justificante**: PDF.
- La extracción automática de datos del PDF (NIF, modelo, periodo) queda **diferida a una versión futura**.
- Se puede reemplazar un fichero subido por error (guardando el anterior en histórico).

---

### 5.6 Anexos de una Declaración

Cada declaración presentada puede tener cero o más anexos. Su propósito es conservar el **contexto de trabajo** del asesor: documentación de soporte, bases de cálculo, aplazamientos solicitados, requerimientos recibidos, etc. Son de uso interno del despacho y no se muestran al cliente en el portal.

**Qué se puede adjuntar:**

- Ficheros PDF (aplazamiento, requerimiento, respuesta a la AEAT...)
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

---

### 5.7 Estados de Cumplimiento

Por cada obligación en un periodo concreto:

| Estado | Descripción |
|---|---|
| `Pendiente` | Dentro de plazo, sin presentación registrada |
| `Presentado` | Fichero PDF subido, dentro del plazo |
| `Presentado fuera de plazo` | Fichero PDF subido, pero la fecha de presentación supera la fecha límite |
| `Sin actividad` | Declaración negativa, exenta o sin actividad, registrada |
| `Incumplido` | Plazo vencido sin presentación registrada |

---

### 5.7 Vistas y Filtros

#### Vista global (todos los clientes del despacho)
- Tabla con todas las obligaciones/declaraciones.
- Filtros:
  - Por cliente o empresa (búsqueda por nombre/NIF)
  - Por asesor/empleado responsable
  - Por modelo fiscal (303, 111, 190...)
  - Por periodo/ejercicio
  - Por estado de cumplimiento
- Acceso: asesores y administradores.

#### Vista por cliente/empresa
- Ficha del cliente con sus empresas asociadas.
- Por empresa: listado de sus obligaciones y estado de cada periodo.
- Histórico de ficheros subidos con opción de descarga.

#### Vista por asesor
- Listado de clientes asignados al asesor con su % de cumplimiento global.
- Un asesor puede consultar también la vista de sus compañeros (lectura).

---

### 5.8 Dashboard

Panel principal diferenciado por rol.

**Dashboard del asesor:**
- Próximos vencimientos de mis clientes (configurable: próximos N días).
- Mis declaraciones pendientes de subir (obligaciones sin fichero dentro de plazo).
- Mis incumplimientos (plazo vencido sin presentación).
- Resumen por modelo fiscal: cuántos presentados, cuántos pendientes, cuántos incumplidos.

**Dashboard del administrador** (además de lo anterior):
- Indicadores globales del despacho: % cumplimiento total, por asesor, por modelo.
- Alertas de nuevos modelos detectados en el calendario AEAT pendientes de revisión.

---

### 5.9 Notificaciones

- Avisos automáticos por email para vencimientos próximos sin presentar:
  - 7 días antes del vencimiento
  - 1 día antes
  - Día de vencimiento
- **Proveedor de email**: SMTP externo (Office 365 o similar). Configuración por variables de entorno.
- No es crítico para el MVP; se puede activar en una fase posterior.
- Notificaciones internas en la app (bandeja de avisos).

---

## 6. Arquitectura Técnica

### 6.1 Stack
| Capa | Tecnología |
|---|---|
| Frontend | TypeScript + React (framework TBD: Next.js o Vite+React) |
| Backend API | Python + FastAPI |
| Base de datos | PostgreSQL |
| ORM | SQLAlchemy + Alembic (migraciones) |
| Autenticación | JWT (access + refresh tokens) + MFA (pyotp para TOTP) |
| Almacenamiento | Sistema de ficheros del VPS (ruta configurable) |
| Tarea periódica | Celery + Redis (o APScheduler) para sincronización ICS y alertas |
| Despliegue | Docker Compose en VPS |

### 6.2 Consideraciones de Diseño Multi-Tenant (futuro)
Aunque el sistema arranca como single-tenant, se recomienda:
- Añadir un campo `tenant_id` en las tablas principales desde el inicio.
- Aislar la configuración (SMTP, calendarios AEAT, etc.) a nivel de tenant.
- Usar subdominios o cabecera HTTP para identificar el tenant en futuras versiones.

### 6.3 Seguridad
- Contraseñas hasheadas con bcrypt.
- Secretos MFA cifrados en base de datos (AES o similar).
- HTTPS obligatorio en el VPS (Let's Encrypt).
- Tokens JWT de corta duración con refresh token rotativo.
- Control de acceso por rol en cada endpoint (RBAC).
- Los ficheros PDF no son accesibles directamente por URL; se sirven a través de la API con validación de permisos.

---

## 7. Plan de Desarrollo por Fases

### Fase 1 — MVP
- Autenticación con MFA (TOTP en primera iteración).
- CRUD de clientes, empresas y obligaciones fiscales.
- Catálogo de modelos fiscales (manual).
- Subida de ficheros PDF y registro de declaraciones.
- Estados de cumplimiento.
- Vista global con filtros básicos (cliente, modelo, estado).
- Dashboard básico del asesor.
- Importación inicial CSV/Excel de clientes.

### Fase 2
- Portal del cliente (acceso con email + MFA).
- Sincronización ICS de la AEAT + vista de revisión del admin.
- Dashboard del administrador con indicadores globales.
- MFA por SMS y por email (además de TOTP).
- Notificaciones por email (vencimientos).

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
| Rendimiento | Listados y filtros con respuesta < 1s para el volumen previsto |
| Seguridad | Datos fiscales sensibles: HTTPS, cifrado, RBAC, sin URLs directas a ficheros |
| Usabilidad | Interfaz orientada a revisión rápida del estado; mínimo de clics para subir un fichero |
| Disponibilidad | VPS con backups periódicos de BD y ficheros |
| Trazabilidad | Cada declaración tiene su fichero adjunto y el usuario/fecha de subida |

---

## 9. Supuestos y Decisiones

- El sistema NO confecciona ni presenta declaraciones: solo registra y controla las ya presentadas.
- La fuente de verdad son los ficheros PDF descargados de la sede electrónica de la AEAT.
- Un cliente (persona/entidad titular) puede tener varias empresas; las obligaciones son por empresa.
- Las fechas de vencimiento se gestionan por periodo para preservar el histórico ante cambios futuros.
- No se implementa auditoría completa en la Fase 1.
- El MFA es obligatorio para todos los usuarios desde el primer acceso.

---

## 10. Riesgos

| Riesgo | Mitigación |
|---|---|
| Variabilidad en formatos PDF de la AEAT | Parseo automático diferido a Fase 3; por ahora entrada manual |
| Cambios en el formato del ICS de la AEAT | Capa de adaptación configurable; revisión manual antes de confirmar cambios |
| Pérdida de ficheros en el VPS | Backups periódicos automatizados; considerar MinIO en el futuro |
| Escalabilidad del VPS | Arquitectura dockerizada facilita migración a cloud si fuera necesario |
| Cumplimiento RGPD | Datos fiscales sensibles; definir política de retención y acceso |
