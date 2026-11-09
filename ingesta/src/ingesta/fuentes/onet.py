# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Carga de O*NET: ocupaciones y matriz de ocupaciones relacionadas (base del Sankey).

Fuente: base de datos O*NET en formato texto (https://www.onetcenter.org/database.html),
licencia CC BY 4.0. Si los ficheros no están en el directorio local, se descarga el zip
oficial (variable ONET_URL) y se extraen solo los dos ficheros necesarios.
"""

import io
import logging
import zipfile
from collections.abc import Iterator
from pathlib import Path

import httpx

from gemelo_core.config import ajustes
from gemelo_core.db import sesion
from gemelo_core.modelos import OcupacionOnet, TransicionOnet
from ingesta.fuentes._util import leer_csv, lotes, upsert

log = logging.getLogger(__name__)

FICHEROS = ("Occupation Data.txt", "Related Occupations.txt")


def filas_ocupaciones(ruta: Path) -> Iterator[dict]:
    for f in leer_csv(ruta, delimitador="\t"):
        yield {"codigo": f["O*NET-SOC Code"], "titulo": f["Title"].strip()}


def filas_transiciones(ruta: Path) -> Iterator[dict]:
    for f in leer_csv(ruta, delimitador="\t"):
        yield {
            "origen": f["O*NET-SOC Code"],
            "destino": f["Related O*NET-SOC Code"],
            "nivel": f["Relatedness Tier"].strip(),
            "indice": int(f["Index"]),
        }


def extraer(contenido_zip: bytes, directorio: Path) -> None:
    """Extrae del zip de O*NET solo los ficheros necesarios, sin respetar sus rutas internas."""
    directorio.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(contenido_zip)) as z:
        por_nombre = {Path(n).name: n for n in z.namelist()}
        for fichero in FICHEROS:
            if fichero not in por_nombre:
                raise ValueError(f"El zip de O*NET no contiene «{fichero}»")
            (directorio / fichero).write_bytes(z.read(por_nombre[fichero]))


def descargar(directorio: Path) -> None:
    url = ajustes().onet_url
    log.info("Descargando O*NET desde %s", url)
    r = httpx.get(url, follow_redirects=True, timeout=300)
    r.raise_for_status()
    extraer(r.content, directorio)


def cargar(directorio: Path) -> None:
    if not all((directorio / f).exists() for f in FICHEROS):
        descargar(directorio)

    pasos = [
        (FICHEROS[0], OcupacionOnet, filas_ocupaciones, ["codigo"]),
        (FICHEROS[1], TransicionOnet, filas_transiciones, ["origen", "destino"]),
    ]
    for fichero, modelo, generador, claves in pasos:
        total = 0
        with sesion() as s:
            for lote in lotes(generador(directorio / fichero)):
                upsert(s, modelo, lote, claves)
                total += len(lote)
        log.info("O*NET %s: %d filas", modelo.__tablename__, total)
