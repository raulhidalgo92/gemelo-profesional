# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import SesionDB
from gemelo_core import __version__

router = APIRouter()


class EstadoSalud(BaseModel):
    estado: str
    version: str
    base_datos: bool


@router.get("/salud", response_model=EstadoSalud)
def salud(db: SesionDB) -> EstadoSalud:
    """Comprueba que la API responde y que la base de datos es accesible."""
    try:
        db.execute(text("SELECT 1"))
        bd_ok = True
    except SQLAlchemyError:
        bd_ok = False
    return EstadoSalud(estado="ok" if bd_ok else "degradado", version=__version__, base_datos=bd_ok)
