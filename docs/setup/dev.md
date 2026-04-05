# Entorno de desarrollo local

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) >= 4.x
- Git

No es necesario instalar Python, Node ni PostgreSQL en la máquina host. Todo corre en contenedores.

---

## Primeros pasos

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd asesoria
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Los valores de `.env.example` son válidos para desarrollo local. No hace falta cambiar nada para arrancar por primera vez.

### 3. Construir y arrancar los servicios

```bash
docker compose up --build
```

La primera vez descarga imágenes y construye contenedores (~3-5 min). Las siguientes veces arranca en segundos.

Servicios que se levantan:
- **db** — PostgreSQL 16 (puerto 5432)
- **db_test** — PostgreSQL 16 para tests (puerto 5433)
- **backend** — FastAPI con hot-reload (puerto 8000)
- **frontend** — React/Vite con hot-reload (puerto 5173)

### 4. Verificar que todo funciona

```bash
# API backend
curl http://localhost:8000/health
# Respuesta esperada: {"status":"ok"}
```

Abrir [http://localhost:5173](http://localhost:5173) en el navegador → pantalla "en construcción".

### 5. Aplicar migraciones de base de datos

```bash
make migrate
```

### 6. Ejecutar los tests

```bash
make test
```

### 7. Auditoría de seguridad de dependencias

```bash
make audit
```

---

## Comandos disponibles

| Comando | Descripción |
|---|---|
| `make up` | Arranca todos los servicios |
| `make down` | Para y elimina los contenedores |
| `make build` | Reconstruye las imágenes Docker |
| `make test` | Ejecuta toda la suite de tests |
| `make migrate` | Aplica migraciones de base de datos |
| `make audit` | Auditoría de seguridad de dependencias |
| `make lint` | Linting y verificación de formato |
| `make shell-backend` | Shell interactivo en el contenedor backend |

---

## Pre-commit hooks

Los hooks formatean el código automáticamente y ejecutan los tests unitarios antes de cada commit.

```bash
# Instalar (solo una vez, requiere pip en PATH)
pip install pre-commit
pre-commit install
```

> Los hooks requieren que Docker esté corriendo, ya que los tests del backend se ejecutan dentro del contenedor.

---

## Puertos de referencia

| Servicio | URL |
|---|---|
| Backend API | http://localhost:8000 |
| Docs interactivos (Swagger) | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |
| PostgreSQL (principal) | localhost:5432 |
| PostgreSQL (tests) | localhost:5433 |
