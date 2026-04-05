FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

RUN pip install --no-cache-dir --upgrade pip

# Copiar solo pyproject.toml primero para aprovechar la caché de capas Docker:
# las dependencias solo se reinstalan si cambia pyproject.toml, no el código.
COPY pyproject.toml .

# Stub mínimo para que pip pueda instalar el paquete en modo editable
RUN mkdir -p app && touch app/__init__.py && \
    pip install --no-cache-dir -e ".[dev]"

# Copiar el código fuente (sobreescribe el stub anterior)
COPY . .

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
