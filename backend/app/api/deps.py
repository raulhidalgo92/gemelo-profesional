# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Dependencias comunes de los endpoints."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from gemelo_core.db import FabricaSesiones


def obtener_sesion() -> Iterator[Session]:
    s = FabricaSesiones()
    try:
        yield s
    finally:
        s.close()


SesionDB = Annotated[Session, Depends(obtener_sesion)]
