# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Tabla de correspondencias oficial ESCO ↔ O*NET.

Publicada por el Secretariado de ESCO junto con el Departamento de Trabajo de EE. UU.
(versión 1, septiembre de 2022: ESCO v1.1.0 ↔ O*NET-SOC 2019). Es el puente que permite
usar la matriz de ocupaciones relacionadas de O*NET con ocupaciones ESCO.

El CSV empieza con un bloque de metadatos; la tabla real arranca en la fila «O*NET Id».
Tipos de correspondencia (SKOS): exactMatch, closeMatch, broadMatch, narrowMatch y
exactISCO (esta última apunta a un grupo ISCO, no a una ocupación ESCO, y se descarta).
"""

import csv
import io
import logging
from collections.abc import Iterator
from pathlib import Path

import httpx
from sqlalchemy import select

from gemelo_core.config import ajustes
from gemelo_core.db import sesion
from gemelo_core.modelos import MapeoEscoOnet, Ocupacion, OcupacionOnet
from ingesta.fuentes._util import lotes, upsert

log = logging.getLogger(__name__)

FICHERO = "esco_onet.csv"
PREFIJO_OCUPACION_ESCO = "http://data.europa.eu/esco/occupation/"


def filas(texto: str) -> Iterator[dict]:
    """Devuelve las correspondencias ocupación ESCO ↔ O*NET del CSV oficial."""
    lineas = texto.lstrip("﻿").splitlines()
    inicio = next(i for i, linea in enumerate(lineas) if linea.startswith("O*NET Id,"))
    for f in csv.DictReader(io.StringIO("\n".join(lineas[inicio:]))):
        uri = (f.get("ESCO or ISCO URI") or "").strip()
        codigo = (f.get("O*NET Id") or "").strip()
        if not codigo or not uri.startswith(PREFIJO_OCUPACION_ESCO):
            continue
        yield {
            "ocupacion_uri": uri,
            "onet_codigo": codigo,
            "tipo_correspondencia": (f.get("Type of Match") or "").strip() or None,
        }


def descargar(ruta: Path) -> None:
    url = ajustes().esco_onet_url
    log.info("Descargando correspondencias ESCO ↔ O*NET desde %s", url)
    r = httpx.get(url, follow_redirects=True, timeout=120)
    r.raise_for_status()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(r.content)


def cargar(directorio: Path) -> None:
    ruta = directorio / FICHERO
    if not ruta.exists():
        descargar(ruta)

    with sesion() as s:
        esco = set(s.scalars(select(Ocupacion.uri)))
        onet = set(s.scalars(select(OcupacionOnet.codigo)))
    if not esco or not onet:
        raise RuntimeError("Carga antes ESCO (esco-api) y O*NET (onet)")

    validas, sin_esco, sin_onet = {}, 0, 0
    for f in filas(ruta.read_text(encoding="utf-8")):
        if f["ocupacion_uri"] not in esco:
            sin_esco += 1
        elif f["onet_codigo"] not in onet:
            sin_onet += 1
        else:
            validas[(f["ocupacion_uri"], f["onet_codigo"])] = f

    with sesion() as s:
        for lote in lotes(validas.values()):
            upsert(s, MapeoEscoOnet, lote, ["ocupacion_uri", "onet_codigo"])
    log.info(
        "ESCO ↔ O*NET: %d correspondencias (%d sin ocupación ESCO actual, %d sin código O*NET)",
        len(validas),
        sin_esco,
        sin_onet,
    )
