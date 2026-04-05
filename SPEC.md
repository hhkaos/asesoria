# Especificación Funcional
## Plataforma Web para Control de Declaraciones Fiscales Presentadas

### 1. Objetivo

Desarrollar una aplicación web para un despacho de asesoría fiscal que permita **controlar y hacer seguimiento de las declaraciones fiscales ya presentadas** ante la AEAT.

El sistema **no confecciona ni rellena declaraciones**. Su función es registrar el estado de cumplimiento de las obligaciones fiscales de cada cliente, tomando como fuente los ficheros descargados directamente de la sede electrónica de la AEAT.

---

### 2. Alcance

Sistema orientado a despachos con gran volumen de clientes (miles), con múltiples usuarios y roles.

---

### 3. Tipos de Usuario

#### 3.1 Administrador
- Gestión completa del sistema
- Alta/baja de usuarios
- Configuración global

#### 3.2 Asesor / Empleado
- Gestión de clientes asignados
- Subida de ficheros AEAT
- Consulta y seguimiento del estado de cumplimiento

---

### 4. Entidades Principales

#### 4.1 Cliente
- ID
- Nombre / Razón social
- NIF/CIF
- Tipo (autónomo, empresa, etc.)
- Datos de contacto
- Asesor/empleado responsable asignado

#### 4.2 Obligación Fiscal
Define qué declaraciones debe presentar cada cliente y cuándo.

- Cliente
- Tipo de modelo (ej: 303, 130, 111, 190, 347...)
- Periodicidad (mensual, trimestral, anual)
- Ejercicio y periodo (ej: 2024-T1)
- Fecha límite de presentación

#### 4.3 Declaración Presentada
Representa una declaración concreta ya presentada ante la AEAT.

- Obligación fiscal asociada
- Fecha de presentación
- Número de justificante
- Resultado (a ingresar, a devolver, sin actividad...)
- Importe (si aplica)
- Fichero AEAT adjunto (PDF/XML descargado de la sede electrónica)
- Estado de cumplimiento (ver sección 5.3)

---

### 5. Funcionalidades

#### 5.1 Gestión de Clientes
- Alta, edición y eliminación
- Asignación de obligaciones fiscales periódicas
- Asignación de asesor/empleado responsable
- Segmentación por tipo de cliente

---

#### 5.2 Subida de Ficheros AEAT

El flujo principal del sistema:

1. El asesor descarga el justificante/acuse de recibo desde la sede electrónica de la AEAT (PDF o XML).
2. Sube el fichero en la aplicación, asociándolo al cliente, modelo y periodo correspondiente.
3. El sistema registra la presentación y actualiza el estado de cumplimiento de esa obligación.

- Formatos admitidos: PDF y XML de la AEAT
- Asociación manual o asistida (por NIF/CIF y modelo detectados en el fichero)
- Posibilidad de adjuntar varios ficheros por declaración

---

#### 5.3 Control de Cumplimiento

**Estados posibles por obligación:**
- `Pendiente` — dentro de plazo, sin presentar
- `Presentado` — fichero AEAT adjunto, en plazo
- `Presentado fuera de plazo` — fichero AEAT adjunto, fecha posterior al límite
- `Sin actividad` — declaración negativa o exenta, registrada
- `Incumplido` — plazo vencido sin presentación registrada

**Indicadores:**
- % de cumplimiento por cliente
- % de cumplimiento por asesor/empleado
- % global del despacho
- Alertas por vencimientos próximos sin presentar

---

#### 5.4 Vistas y Filtros

**Vista general (todas las obligaciones):**
- Tabla con todas las declaraciones del despacho
- Filtro por cliente
- Filtro por asesor/empleado responsable
- Filtro por modelo (303, 111, 190...)
- Filtro por periodo/ejercicio
- Filtro por estado de cumplimiento

**Vista por cliente:**
- Listado de todas sus obligaciones y su estado
- Histórico de declaraciones presentadas con ficheros adjuntos

**Vista por asesor/empleado:**
- Listado de todos los clientes asignados y su grado de cumplimiento

---

#### 5.5 Dashboard

Panel principal con:
- Próximos vencimientos sin presentar
- Declaraciones presentadas hoy / esta semana
- Indicadores de cumplimiento global, por empleado y por cliente
- Alertas de incumplimientos (plazo vencido sin fichero)

---

#### 5.6 Notificaciones

- Avisos automáticos por vencimientos próximos sin presentar:
  - 7 días antes
  - 1 día antes
  - Día de vencimiento
- Tipos: email y notificación interna

---

### 6. Requisitos No Funcionales

#### 6.1 Escalabilidad
- Soporte para miles de clientes y miles de declaraciones anuales

#### 6.2 Seguridad
- Autenticación de usuarios
- Control de acceso por roles
- Protección de datos fiscales sensibles

#### 6.3 Usabilidad
- Interfaz clara orientada a revisión rápida del estado de cumplimiento
- Navegación ágil entre clientes y periodos

#### 6.4 Rendimiento
- Carga rápida de listados y filtros
- Búsqueda eficiente por NIF, nombre, modelo y periodo

---

### 7. Posibles Extensiones Futuras

- Parseo automático del NIF/modelo/periodo desde el fichero AEAT al subirlo
- Portal cliente para que vea el estado de sus propias declaraciones
- Integración con la API de la AEAT (consulta directa)
- Exportación de informes de cumplimiento

---

### 8. Supuestos y Decisiones

- El sistema **no confecciona ni presenta declaraciones**: solo registra y controla las ya presentadas.
- La fuente de verdad son los ficheros descargados de la sede electrónica de la AEAT.
- Cada cliente puede tener múltiples obligaciones fiscales de distintos modelos y periodicidades.
- Cada obligación puede estar asignada a un asesor/empleado responsable del seguimiento.

---

### 9. Riesgos

- Variabilidad en los formatos de ficheros de la AEAT según el modelo
- Escalabilidad con gran volumen de documentos adjuntos
- Cumplimiento normativo (protección de datos fiscales)

---

### 10. Métricas de Éxito

- Visibilidad completa del estado de cumplimiento del despacho en tiempo real
- Reducción de incumplimientos por olvido o falta de seguimiento
- Ahorro de tiempo en revisión manual del estado de cada cliente
- Trazabilidad completa: cada declaración tiene su justificante AEAT adjunto
