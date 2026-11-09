# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Carga de ESCO (español) desde su API REST oficial.

Alternativa a la descarga manual en CSV (`esco.py`): no requiere ficheros y
permite reproducir la carga en cualquier entorno. Flujo:
  1. /search pagina todas las URIs de competencias y ocupaciones.
  2. /resource/{tipo}?uris=...&uris=... obtiene el detalle por lotes.
  3. Se cargan competencias, después ocupaciones y por último sus relaciones.

API: https://ec.europa.eu/esco/api (documentación en esco.ec.europa.eu).
"""

import logging
import time
from collections.abc import Iterator

import httpx
from sqlalchemy import select

from gemelo_core.config import ajustes
from gemelo_core.db import sesion
from gemelo_core.modelos import Competencia, Ocupacion, OcupacionCompetencia
from ingesta.fuentes._util import lotes, upsert

log = logging.getLogger(__name__)

IDIOMA = "es"
TAM_PAGINA = 500
TAM_LOTE_DETALLE = 50
PAUSA_SEGUNDOS = 0.2  # cortesía con el servicio público


# --- Normalización (funciones puras) ---------------------------------------------------------


def _ultimo_segmento(uri: str | None) -> str | None:
    return uri.rstrip("/").rsplit("/", 1)[-1] if uri else None


def _texto(campo: dict | None) -> str | None:
    """Extrae el texto en español de un campo multilingüe de ESCO."""
    valor = (campo or {}).get(IDIOMA)
    if isinstance(valor, dict):
        valor = valor.get("literal")
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def _alternativos(concepto: dict) -> str | None:
    etiquetas = (concepto.get("alternativeLabel") or {}).get(IDIOMA) or []
    return "\n".join(etiquetas) or None


def _primer_enlace(concepto: dict, relacion: str) -> dict:
    enlaces = (concepto.get("_links") or {}).get(relacion) or []
    return enlaces[0] if enlaces else {}


def normalizar_competencia(c: dict) -> dict:
    return {
        "uri": c["uri"],
        "titulo": _texto(c.get("preferredLabel")) or c.get("title", ""),
        "titulos_alternativos": _alternativos(c),
        "tipo": _ultimo_segmento(_primer_enlace(c, "hasSkillType").get("uri")),
        "nivel_reutilizacion": _ultimo_segmento(_primer_enlace(c, "hasReuseLevel").get("uri")),
        "descripcion": _texto(c.get("description")),
    }


def normalizar_ocupacion(o: dict) -> dict:
    isco = _primer_enlace(o, "broaderIscoGroup")
    grupo = isco.get("code") or (_ultimo_segmento(isco.get("uri")) or "").lstrip("C") or None
    return {
        "uri": o["uri"],
        "codigo": o.get("code"),
        "grupo_isco": grupo,
        "titulo": _texto(o.get("preferredLabel")) or o.get("title", ""),
        "titulos_alternativos": _alternativos(o),
        "descripcion": _texto(o.get("description")),
    }


def relaciones_de(o: dict) -> Iterator[dict]:
    enlaces = o.get("_links") or {}
    for clave, relacion in (("hasEssentialSkill", "essential"), ("hasOptionalSkill", "optional")):
        for e in enlaces.get(clave) or []:
            yield {"ocupacion_uri": o["uri"], "competencia_uri": e["uri"], "relacion": relacion}


# --- Acceso a la API ---------------------------------------------------------------------------


def _get(http: httpx.Client, ruta: str, params: list[tuple[str, str]] | dict) -> dict:
    for intento in range(4):
        try:
            r = http.get(ruta, params=params)
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as e:
            if intento == 3:
                raise
            espera = 2**intento
            log.warning("ESCO %s falló (%s); reintento en %ss", ruta, e, espera)
            time.sleep(espera)
    raise RuntimeError("inalcanzable")


def listar_uris(http: httpx.Client, tipo: str) -> list[str]:
    """Pagina /search. Ojo: en la API de ESCO `offset` es el NÚMERO DE PÁGINA, no de elementos."""
    uris: list[str] = []
    pagina = 0
    while True:
        datos = _get(
            http,
            "/search",
            {
                "type": tipo,
                "language": IDIOMA,
                "limit": TAM_PAGINA,
                "offset": pagina,
                "full": "false",
            },
        )
        resultados = datos.get("_embedded", {}).get("results", [])
        uris.extend(r["uri"] for r in resultados)
        pagina += 1
        if not resultados or len(uris) >= datos.get("total", 0):
            # Eliminar duplicados conservando el orden
            return list(dict.fromkeys(uris))
        time.sleep(PAUSA_SEGUNDOS)


def _detalle_lote(
    http: httpx.Client, tipo: str, lote: list[str], fallidas: list[str]
) -> list[dict]:
    """Descarga un lote; si falla tras los reintentos, lo parte en dos para aislar la URI mala."""
    params = [("language", IDIOMA)] + [("uris", u) for u in lote]
    try:
        return list(_get(http, f"/resource/{tipo}", params).get("_embedded", {}).values())
    except (httpx.HTTPStatusError, httpx.TransportError):
        if len(lote) == 1:
            log.error("ESCO: no se pudo descargar %s; se omite", lote[0])
            fallidas.append(lote[0])
            return []
        mitad = len(lote) // 2
        return _detalle_lote(http, tipo, lote[:mitad], fallidas) + _detalle_lote(
            http, tipo, lote[mitad:], fallidas
        )


def detalles(
    http: httpx.Client, tipo: str, uris: list[str], fallidas: list[str] | None = None
) -> Iterator[dict]:
    fallidas = [] if fallidas is None else fallidas
    for lote in lotes(uris, TAM_LOTE_DETALLE):
        yield from _detalle_lote(http, tipo, lote, fallidas)
        time.sleep(PAUSA_SEGUNDOS)


# --- Carga -------------------------------------------------------------------------------------


def cargar() -> None:
    """Carga idempotente; cada bloque se confirma por separado para no perder progreso."""
    fallidas: list[str] = []
    with httpx.Client(base_url=ajustes().esco_api_url, timeout=60) as http:
        uris_comp = listar_uris(http, "skill")
        log.info("ESCO: %d competencias a descargar", len(uris_comp))
        hechas = 0
        for lote in lotes(detalles(http, "skill", uris_comp, fallidas), 500):
            with sesion() as s:
                upsert(s, Competencia, [normalizar_competencia(c) for c in lote], ["uri"])
            hechas += len(lote)
            log.info("ESCO competencias: %d/%d", hechas, len(uris_comp))

        with sesion() as s:
            conocidas = set(s.scalars(select(Competencia.uri)))

        uris_ocup = listar_uris(http, "occupation")
        log.info("ESCO: %d ocupaciones a descargar", len(uris_ocup))
        total_ocup = total_rel = 0
        for lote in lotes(detalles(http, "occupation", uris_ocup, fallidas), 200):
            relaciones = {
                (r["ocupacion_uri"], r["competencia_uri"]): r
                for o in lote
                for r in relaciones_de(o)
                if r["competencia_uri"] in conocidas
            }
            with sesion() as s:
                upsert(s, Ocupacion, [normalizar_ocupacion(o) for o in lote], ["uri"])
                for sub in lotes(relaciones.values(), 2000):
                    upsert(s, OcupacionCompetencia, sub, ["ocupacion_uri", "competencia_uri"])
            total_ocup += len(lote)
            total_rel += len(relaciones)
            log.info("ESCO ocupaciones: %d/%d", total_ocup, len(uris_ocup))

    log.info(
        "ESCO completado: %d competencias, %d ocupaciones, %d relaciones, %d URIs omitidas",
        hechas,
        total_ocup,
        total_rel,
        len(fallidas),
    )
