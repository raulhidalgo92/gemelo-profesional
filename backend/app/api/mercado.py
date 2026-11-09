# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Resumen del estado de los datos de mercado cargados por la ingesta."""

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import SesionDB
from gemelo_core.modelos import Competencia, Ocupacion, Oferta, TransicionOnet

router = APIRouter()


class ResumenMercado(BaseModel):
    ocupaciones: int
    competencias: int
    transiciones: int
    ofertas: int
    ofertas_por_fuente: dict[str, int]


@router.get("/resumen", response_model=ResumenMercado)
def resumen(db: SesionDB) -> ResumenMercado:
    def contar(modelo) -> int:
        return db.scalar(select(func.count()).select_from(modelo)) or 0

    por_fuente = dict(
        db.execute(select(Oferta.fuente, func.count()).group_by(Oferta.fuente)).tuples().all()
    )
    return ResumenMercado(
        ocupaciones=contar(Ocupacion),
        competencias=contar(Competencia),
        transiciones=contar(TransicionOnet),
        ofertas=contar(Oferta),
        ofertas_por_fuente=por_fuente,
    )
