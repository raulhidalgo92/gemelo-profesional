# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# Contexto de construcción: raíz del repositorio (necesita core/)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /srv
COPY core/ core/
COPY backend/ backend/
RUN pip install -e ./core -e "./backend[dev]"

WORKDIR /srv/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
