# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Búsqueda en el vocabulario ESCO de competencias.

Dos modos:
- «semantico»: compara el significado de la consulta con el de cada competencia
  (embeddings + distancia coseno en pgvector). Encuentra «TypeScript» al buscar «Angular».
- «texto»: similitud de caracteres (pg_trgm). No necesita IA.

Si el modo semántico no está disponible, la búsqueda se resuelve por texto.
"""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import IA, SesionDB
from gemelo_core.ia import TAREA_CONSULTA, ClienteIA, ErrorIA
from gemelo_core.modelos import Competencia

router = APIRouter()
log = logging.getLogger(__name__)

Modo = Literal["semantico", "texto"]


class CompetenciaSalida(BaseModel):
    uri: str
    titulo: str
    tipo: str | None
    similitud: float


class BusquedaSalida(BaseModel):
    modo: Modo
    resultados: list[CompetenciaSalida]


def _por_texto(db: Session, q: str, limite: int) -> list[CompetenciaSalida]:
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


def _por_significado(db: Session, ia: ClienteIA, q: str, limite: int) -> list[CompetenciaSalida]:
    vector = ia.embeddings([q], tarea=TAREA_CONSULTA)[0]
    distancia = Competencia.embedding.cosine_distance(vector)
    consulta = (
        select(Competencia.uri, Competencia.titulo, Competencia.tipo, distancia.label("dist"))
        .where(Competencia.embedding.is_not(None))
        .order_by(distancia)
        .limit(limite)
    )
    return [
        CompetenciaSalida(uri=f.uri, titulo=f.titulo, tipo=f.tipo, similitud=round(1 - f.dist, 3))
        for f in db.execute(consulta)
    ]


@router.get("", response_model=BusquedaSalida)
def buscar(
    db: SesionDB,
    ia: IA,
    q: Annotated[str, Query(min_length=2, description="Texto a buscar")],
    modo: Annotated[Modo, Query(description="semantico (por significado) o texto")] = "semantico",
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
) -> BusquedaSalida:
    if modo == "semantico" and ia is not None:
        try:
            return BusquedaSalida(modo="semantico", resultados=_por_significado(db, ia, q, limite))
        except ErrorIA:
            log.warning("Búsqueda semántica no disponible; se usa la búsqueda por texto")
    return BusquedaSalida(modo="texto", resultados=_por_texto(db, q, limite))
