# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Carga de la clasificación ESCO desde su descarga oficial en CSV (idioma: español).

Descarga: https://esco.ec.europa.eu/en/use-esco/download (formato CSV, idioma «es»).
Ficheros esperados en el directorio: occupations_es.csv, skills_es.csv,
occupationSkillRelations_es.csv.
"""

import logging
from collections.abc import Iterator
from pathlib import Path

from gemelo_core.db import sesion
from gemelo_core.modelos import Competencia, Ocupacion, OcupacionCompetencia
from ingesta.fuentes._util import leer_csv, lotes, upsert

log = logging.getLogger(__name__)


def _limpio(valor: str | None) -> str | None:
    valor = (valor or "").strip()
    return valor or None


def filas_ocupaciones(ruta: Path) -> Iterator[dict]:
    for f in leer_csv(ruta):
        yield {
            "uri": f["conceptUri"],
            "codigo": _limpio(f.get("code")),
            "grupo_isco": _limpio(f.get("iscoGroup")),
            "titulo": f["preferredLabel"].strip(),
            "titulos_alternativos": _limpio(f.get("altLabels")),
            "descripcion": _limpio(f.get("description")),
        }


def filas_competencias(ruta: Path) -> Iterator[dict]:
    for f in leer_csv(ruta):
        yield {
            "uri": f["conceptUri"],
            "titulo": f["preferredLabel"].strip(),
            "titulos_alternativos": _limpio(f.get("altLabels")),
            "tipo": _limpio(f.get("skillType")),
            "nivel_reutilizacion": _limpio(f.get("reuseLevel")),
            "descripcion": _limpio(f.get("description")),
        }


def filas_relaciones(ruta: Path) -> Iterator[dict]:
    for f in leer_csv(ruta):
        yield {
            "ocupacion_uri": f["occupationUri"],
            "competencia_uri": f["skillUri"],
            "relacion": f["relationType"].strip(),
        }


def cargar(directorio: Path) -> None:
    pasos = [
        ("occupations_es.csv", Ocupacion, filas_ocupaciones, ["uri"]),
        ("skills_es.csv", Competencia, filas_competencias, ["uri"]),
        (
            "occupationSkillRelations_es.csv",
            OcupacionCompetencia,
            filas_relaciones,
            ["ocupacion_uri", "competencia_uri"],
        ),
    ]
    for fichero, modelo, generador, claves in pasos:
        ruta = directorio / fichero
        if not ruta.exists():
            raise FileNotFoundError(f"No se encuentra {ruta}. Descarga ESCO en CSV (español).")
        total = 0
        with sesion() as s:
            for lote in lotes(generador(ruta)):
                upsert(s, modelo, lote, claves)
                total += len(lote)
        log.info("ESCO %s: %d filas", modelo.__tablename__, total)
