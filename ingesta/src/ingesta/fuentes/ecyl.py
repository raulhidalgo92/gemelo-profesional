# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Ofertas del Servicio Público de Empleo de Castilla y León (ECyL).

Datos abiertos de la Junta de Castilla y León con licencia CC BY 4.0, actualizados a
diario. Incluye ofertas propias del ECyL, de organismos oficiales, de EURES y de prensa.
Algunas descripciones traen teléfonos, emails o nombres de contacto: se eliminan antes
de guardarlas.
"""

from collections.abc import Iterable, Iterator
from datetime import date

import httpx

from ingesta.fuentes._ofertas import guardar, texto_plano

FUENTE = "ecyl"
URL = (
    "https://analisis.datosabiertos.jcyl.es/api/explore/v2.1/catalog/datasets/"
    "ofertas-de-empleo/exports/json"
)


def _fecha(valor: str | None) -> date | None:
    try:
        return date.fromisoformat(valor) if valor else None
    except ValueError:
        return None


def normalizar(registro: dict) -> dict:
    """Convierte un registro del conjunto de datos al esquema común `oferta`."""
    return {
        "fuente": FUENTE,
        "id_externo": str(registro["identificador"]),
        "titulo": texto_plano(registro.get("titulo"))[:512],
        "empresa": None,
        "provincia": registro.get("provincia") or None,
        "ubicacion": registro.get("localidad_asset0") or None,
        "salario_min": None,
        "salario_max": None,
        "salario_periodo": None,
        "texto": texto_plano(registro.get("descripcion")),
        "url": (registro.get("enlace_al_contenido") or "")[:1024] or None,
        "publicada_en": _fecha(registro.get("fecha_publicacion")),
    }


def filas(registros: Iterable[dict]) -> Iterator[dict]:
    for registro in registros:
        if registro.get("identificador") and registro.get("titulo"):
            yield normalizar(registro)


def ingerir() -> int:
    r = httpx.get(URL, params={"lang": "es", "timezone": "Europe/Madrid"}, timeout=120)
    r.raise_for_status()
    return guardar(FUENTE, list(filas(r.json())))
