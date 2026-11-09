# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Dependencias comunes de los endpoints."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from gemelo_core.db import FabricaSesiones
from gemelo_core.ia import ClienteIA, ErrorIA, cliente_ia


def obtener_sesion() -> Iterator[Session]:
    s = FabricaSesiones()
    try:
        yield s
    finally:
        s.close()


def obtener_cliente_ia() -> ClienteIA | None:
    """Cliente de IA, o None si no está configurado (los endpoints deben degradarse)."""
    try:
        return cliente_ia()
    except ErrorIA:
        return None


SesionDB = Annotated[Session, Depends(obtener_sesion)]
IA = Annotated[ClienteIA | None, Depends(obtener_cliente_ia)]
