# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Utilidades comunes de carga masiva."""

import csv
from collections.abc import Iterable, Iterator
from itertools import islice
from pathlib import Path
from typing import Any

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
