# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Utilidades comunes de carga masiva."""

import csv
from collections.abc import Iterable, Iterator
from itertools import islice
from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


def lotes(filas: Iterable[Any], tamano: int = 2000) -> Iterator[list[Any]]:
    it = iter(filas)
    while lote := list(islice(it, tamano)):
        yield lote


def leer_csv(ruta: Path, delimitador: str = ",") -> Iterator[dict[str, str]]:
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f, delimiter=delimitador)


def upsert(s: Session, modelo: type, filas: list[dict], claves: list[str]) -> None:
    """INSERT ... ON CONFLICT DO UPDATE (idempotente: se puede relanzar sin duplicar)."""
    if not filas:
        return
    sentencia = insert(modelo).values(filas)
    actualizables = {c: sentencia.excluded[c] for c in filas[0] if c not in claves}
    if actualizables:
        sentencia = sentencia.on_conflict_do_update(index_elements=claves, set_=actualizables)
    else:
        sentencia = sentencia.on_conflict_do_nothing(index_elements=claves)
    s.execute(sentencia)


def sustituir_vigentes(s: Session, modelo: type, fuente: str, filas: list[dict]) -> tuple[int, int]:
    """Guarda las filas vigentes de una fuente y borra las que ya no aparecen.

    Para fuentes que publican siempre la lista completa (ofertas, cursos). El modelo
    debe tener las columnas `fuente` e `id_externo`. Devuelve (guardadas, borradas).
    Si una fila viene repetida en la fuente, se queda la última.
    """
    filas = list({f["id_externo"]: f for f in filas}.values())
    for lote in lotes(filas, 500):
        upsert(s, modelo, lote, ["fuente", "id_externo"])
    ids = [f["id_externo"] for f in filas]
    borrar = delete(modelo).where(modelo.fuente == fuente, modelo.id_externo.not_in(ids))
    return len(filas), s.execute(borrar).rowcount
