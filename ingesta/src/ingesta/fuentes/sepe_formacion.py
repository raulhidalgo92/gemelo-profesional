# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Catálogo de Especialidades Formativas del SEPE (especialidades e itinerarios).

El SEPE no publica el catálogo como datos abiertos, pero su buscador oficial
(sede.sepe.gob.es) permite exportarlo a Excel. Los ficheros se exportan a mano con
«Solo última versión», sin filtros y con el campo «Ocupaciones relacionadas», y se
guardan en data/raw/sepe/ con la fecha en el nombre:
    especialidades-formativas-AAAAMMDD.xlsx
    itinerarios-formativos-AAAAMMDD.xlsx

Reutilización autorizada por el aviso legal del SEPE (Ley 37/2007 y RD 1495/2011),
citando «Origen de los datos: SEPE» y la fecha de exportación.
"""

import logging
import re
from collections.abc import Iterator
from pathlib import Path

import openpyxl
from sqlalchemy import delete

from gemelo_core.db import sesion
from gemelo_core.modelos import EspecialidadFormativa, EspecialidadOcupacion, ItinerarioFormativo
from ingesta.fuentes._util import lotes, upsert

log = logging.getLogger(__name__)

# «29341012 - AYUDANTES DE DIRECCIÓN DE CINE, 2712 - ANALISTAS Y DISEÑADORES DE SOFTWARE»
# Los códigos tienen 8 dígitos (los 4 primeros son la CNO-11) o solo los 4 de la CNO-11;
# a veces Excel ha perdido los ceros iniciales («111010» es «00111010»).
OCUPACION = re.compile(r"(\d{4,8}) - (.*?)(?=, \d{4,8} - |$)")


def _entero(valor: object) -> int | None:
    try:
        return int(str(valor).strip())
    except ValueError:
        return None


def _texto(valor: object) -> str | None:
    texto = str(valor or "").strip()
    return None if texto in ("", "-", "Sin asignar familia") else texto


def leer_excel(ruta: Path) -> Iterator[dict[str, object]]:
    """Filas de la hoja «Resultados» como diccionarios indexados por la cabecera."""
    hoja = openpyxl.load_workbook(ruta, read_only=False)["Resultados"]
    filas = hoja.iter_rows(values_only=True)
    cabecera = [str(c or "").strip() for c in next(filas)]
    for fila in filas:
        if fila and fila[0]:
            yield dict(zip(cabecera, fila, strict=False))


def ocupaciones(texto: object) -> list[tuple[str, str]]:
    """Separa la celda de ocupaciones relacionadas en pares (código, título)."""
    return [
        (codigo.zfill(8) if len(codigo) > 4 else codigo.zfill(4), titulo.strip(" ,"))
        for codigo, titulo in OCUPACION.findall(str(texto or ""))
    ]


def normalizar_especialidad(f: dict[str, object]) -> dict:
    return {
        "codigo": str(f["CÓDIGO"]).strip(),
        "denominacion": str(f["DENOMINACIÓN"]).strip()[:512],
        "version": _entero(f.get("VERSIÓN")) or 1,
        "familia": _texto(f.get("FAMILIA PROFESIONAL")),
        "area": _texto(f.get("ÁREA PROFESIONAL")),
        "nivel": _entero(f.get("NIVEL DE CUALIFICACIÓN")),
        "modalidad": _texto(f.get("MODALIDAD DE IMPARTICIÓN")),
        "horas": _entero(f.get("DURACIÓN TOTAL")),
        "horas_presenciales": _entero(
            f.get("DURACIÓN TOTAL DE LA PARTE PRESENCIAL (TELEFORMACIÓN O MIXTA)")
        ),
        "competencia_transversal": _texto(f.get("COMPETENCIA TRANSVERSAL")),
    }


def normalizar_itinerario(f: dict[str, object]) -> dict:
    return {
        "codigo": str(f["CÓDIGO"]).strip(),
        "denominacion": str(f["DENOMINACIÓN"]).strip()[:512],
        "version": _entero(f.get("VERSIÓN")) or 1,
        "familia": _texto(f.get("FAMILIA PROFESIONAL")),
        "nivel": _entero(f.get("NIVEL DE CUALIFICACIÓN")),
        "horas": _entero(f.get("DURACIÓN TOTAL")),
        "competencia_transversal": _texto(f.get("COMPETENCIA TRANSVERSAL")),
    }


def _ultimo(directorio: Path, prefijo: str) -> Path:
    ficheros = sorted(directorio.glob(f"{prefijo}-*.xlsx"))
    if not ficheros:
        raise FileNotFoundError(f"No hay ningún {prefijo}-AAAAMMDD.xlsx en {directorio}")
    return ficheros[-1]


def cargar(directorio: Path) -> None:
    ruta = _ultimo(directorio, "especialidades-formativas")
    filas = list(leer_excel(ruta))
    especialidades = [normalizar_especialidad(f) for f in filas]
    relaciones = [
        {
            "especialidad_codigo": e["codigo"],
            "codigo_ocupacion": c,
            "cno": c[:4],
            "titulo": (t or c)[:255],
        }
        for e, f in zip(especialidades, filas, strict=True)
        for c, t in dict(ocupaciones(f.get("OCUPACIONES RELACIONADAS"))).items()
    ]
    itinerarios = [
        normalizar_itinerario(f) for f in leer_excel(_ultimo(directorio, "itinerarios-formativos"))
    ]

    with sesion() as s:
        for lote in lotes(especialidades):
            upsert(s, EspecialidadFormativa, lote, ["codigo"])
        s.execute(delete(EspecialidadOcupacion))  # se reconstruye con el último catálogo
        for lote in lotes(relaciones):
            upsert(s, EspecialidadOcupacion, lote, ["especialidad_codigo", "codigo_ocupacion"])
        for lote in lotes(itinerarios):
            upsert(s, ItinerarioFormativo, lote, ["codigo"])
        s.commit()
    log.info(
        "SEPE (%s): %d especialidades, %d relaciones con ocupaciones, %d itinerarios",
        ruta.name,
        len(especialidades),
        len(relaciones),
        len(itinerarios),
    )
