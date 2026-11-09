# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Consulta del vocabulario ESCO de competencias."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import SesionDB
from gemelo_core.modelos import Competencia

router = APIRouter()


class CompetenciaSalida(BaseModel):
    uri: str
    titulo: str
    tipo: str | None
    similitud: float


@router.get("", response_model=list[CompetenciaSalida])
def buscar(
    db: SesionDB,
    q: str = Query(min_length=2, description="Texto a buscar"),
    limite: int = Query(20, ge=1, le=100),
) -> list[CompetenciaSalida]:
    """Autocompletado de competencias por similitud de trigramas (pg_trgm)."""
    similitud = func.similarity(Competencia.titulo, q)
    consulta = (
        select(Competencia.uri, Competencia.titulo, Competencia.tipo, similitud.label("sim"))
        .where(Competencia.titulo.op("%")(q) | Competencia.titulo.ilike(f"%{q}%"))
        .order_by(similitud.desc())
        .limit(limite)
    )
    return [
        CompetenciaSalida(uri=f.uri, titulo=f.titulo, tipo=f.tipo, similitud=round(f.sim, 3))
        for f in db.execute(consulta)
    ]
