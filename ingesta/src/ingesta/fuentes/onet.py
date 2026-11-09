# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Carga de O*NET: ocupaciones y matriz de ocupaciones relacionadas (base del Sankey).

Descarga: https://www.onetcenter.org/database.html (formato «Text», licencia CC BY 4.0).
Ficheros esperados: «Occupation Data.txt» y «Related Occupations.txt» (tabulados).
"""

import logging
from collections.abc import Iterator
from pathlib import Path

from gemelo_core.db import sesion
from gemelo_core.modelos import OcupacionOnet, TransicionOnet
from ingesta.fuentes._util import leer_csv, lotes, upsert

log = logging.getLogger(__name__)


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


def cargar(directorio: Path) -> None:
    pasos = [
        ("Occupation Data.txt", OcupacionOnet, filas_ocupaciones, ["codigo"]),
        ("Related Occupations.txt", TransicionOnet, filas_transiciones, ["origen", "destino"]),
    ]
    for fichero, modelo, generador, claves in pasos:
        ruta = directorio / fichero
        if not ruta.exists():
            raise FileNotFoundError(f"No se encuentra {ruta}. Descarga la base de datos O*NET.")
        total = 0
        with sesion() as s:
            for lote in lotes(generador(ruta)):
                upsert(s, modelo, lote, claves)
                total += len(lote)
        log.info("O*NET %s: %d filas", modelo.__tablename__, total)
