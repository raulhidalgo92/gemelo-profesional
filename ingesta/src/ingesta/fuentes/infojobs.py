# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Ofertas de la API pública de InfoJobs.

Requiere registrar una aplicación en https://developer.infojobs.net para obtener
client_id y client_secret. El listado de ofertas no necesita token de usuario,
solo autenticación básica con las credenciales de la aplicación.
Revisar la versión de la API y los campos con la documentación oficial.
"""

import logging
from collections.abc import Iterator
from datetime import date, datetime

import httpx

from gemelo_core.config import ajustes
from gemelo_core.db import sesion
from gemelo_core.modelos import Oferta
from ingesta.fuentes._util import upsert

log = logging.getLogger(__name__)
URL_BASE = "https://api.infojobs.net/api"


def _cliente() -> httpx.Client:
    cfg = ajustes()
    if not (cfg.infojobs_client_id and cfg.infojobs_client_secret):
        raise RuntimeError("Faltan INFOJOBS_CLIENT_ID / INFOJOBS_CLIENT_SECRET en .env")
    return httpx.Client(
        base_url=URL_BASE,
        auth=(cfg.infojobs_client_id, cfg.infojobs_client_secret),
        timeout=30,
    )


def _fecha(valor: str | None) -> date | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def normalizar(o: dict) -> dict:
    """Convierte una oferta del listado de InfoJobs al esquema común `oferta`."""
    return {
        "fuente": "infojobs",
        "id_externo": str(o["id"]),
        "titulo": (o.get("title") or "").strip()[:512],
        "empresa": (o.get("author") or {}).get("name"),
        "provincia": (o.get("province") or {}).get("value"),
        "ubicacion": o.get("city"),
        "url": o.get("link"),
        "publicada_en": _fecha(o.get("published")),
        "texto": o.get("requirementMin"),
    }


def paginas_ofertas(consulta: str, paginas: int) -> Iterator[list[dict]]:
    with _cliente() as http:
        for pagina in range(1, paginas + 1):
            r = http.get("/9/offer", params={"q": consulta, "maxResults": 50, "page": pagina})
            r.raise_for_status()
            datos = r.json()
            yield datos.get("offers", [])
            if pagina >= datos.get("totalPages", 0):
                break


def ingerir(consulta: str = "", paginas: int = 5) -> int:
    total = 0
    with sesion() as s:
        for lote in paginas_ofertas(consulta, paginas):
            filas = [normalizar(o) for o in lote]
            upsert(s, Oferta, filas, ["fuente", "id_externo"])
            total += len(filas)
    log.info("InfoJobs: %d ofertas", total)
    return total
