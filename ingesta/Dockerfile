# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# Contexto de construcción: raíz del repositorio (necesita core/)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 TZ=Europe/Madrid

WORKDIR /srv
COPY core/ core/
COPY ingesta/ ingesta/
RUN pip install -e ./core -e "./ingesta[dev]"

WORKDIR /srv/ingesta
CMD ["python", "-m", "ingesta", "programador"]
