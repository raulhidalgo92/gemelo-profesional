# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Cursos de formación ocupacional y continua del Servei Públic d'Ocupació de Catalunya.

Datos abiertos de la Generalitat de Catalunya (catálogo datos.gob.es), un JSON con los
cursos programados que se actualiza cada hora. El fichero no está en UTF-8 sino en
Latin-1, y las fechas vienen como MM/DD/AAAA. Del centro solo se guarda el nombre.
Cita obligatoria: «Generalitat de Catalunya. Departament d'Empresa i Treball».
"""

import json
import logging
from collections.abc import Iterable, Iterator
from datetime import date, datetime

import httpx

from gemelo_core.db import sesion
from gemelo_core.modelos import Curso
from ingesta.fuentes._util import sustituir_vigentes

log = logging.getLogger(__name__)

FUENTE = "cursos_soc"
URL = "https://oficinadetreball.gencat.cat/opendata/recursos/ofertaCursos.json"


def _fecha(valor: str | None) -> date | None:
    try:
        return datetime.strptime(valor or "", "%m/%d/%Y").date()
    except ValueError:
        return None


def _entero(valor: object) -> int | None:
    try:
        return int(str(valor).strip())
    except ValueError:
        return None


def _texto(valor: object, largo: int) -> str | None:
    return str(valor or "").strip()[:largo] or None


def normalizar(c: dict) -> dict:
    """Convierte un curso del JSON al esquema común `curso`."""
    return {
        "fuente": FUENTE,
        "id_externo": str(c["curs"]),
        "denominacion": str(c["especialitat_formativa"]).strip().rstrip(".")[:512],
        "tipo": _texto(c.get("tipus"), 64),
        "modalidad": _texto(c.get("modalitat"), 64),
        "horas": _entero(c.get("hores")),
        "fecha_inicio": _fecha(c.get("data_inici")),
        "fecha_fin": _fecha(c.get("data_fi")),
        "municipio": _texto(c.get("municipi_especialitat"), 128),
        "provincia": (_texto(c.get("provincia_especialitat"), 128) or "").title() or None,
        "centro": _texto(c.get("nom_centre"), 255),
        "estado": _texto(c.get("estat_curs"), 128),
    }


def filas(cursos: Iterable[dict]) -> Iterator[dict]:
    for c in cursos:
        if c.get("curs") and c.get("especialitat_formativa"):
            yield normalizar(c)


def ingerir() -> int:
    r = httpx.get(URL, timeout=120)
    r.raise_for_status()
    cursos = list(filas(json.loads(r.content.decode("latin-1"))))
    if not cursos:
        log.warning("%s: no se ha recibido ningún curso, se conservan los anteriores", FUENTE)
        return 0
    with sesion() as s:
        vigentes, retirados = sustituir_vigentes(s, Curso, FUENTE, cursos)
        s.commit()
    log.info("%s: %d cursos vigentes, %d retirados", FUENTE, vigentes, retirados)
    return vigentes
