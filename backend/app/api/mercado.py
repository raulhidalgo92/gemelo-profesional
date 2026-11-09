# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Datos de mercado: resumen de lo cargado y salarios por ocupación."""

from collections import Counter
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import SesionDB
from gemelo_core.modelos import (
    Competencia,
    CorrespondenciaCnoIsco,
    EstadisticaSalarial,
    Ocupacion,
    Oferta,
    TransicionOnet,
)

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


# Grandes grupos de la CNO-11 (letra) y los subgrupos principales (2 dígitos) que abarcan.
GRANDES_GRUPOS_CNO = {
    "A": range(11, 16), "B": range(21, 24), "C": range(24, 30), "D": range(31, 39),
    "E": range(41, 44), "F": range(44, 46), "G": range(50, 56), "H": range(56, 58),
    "I": range(58, 60), "J": range(61, 65), "K": range(71, 73), "L": range(73, 79),
    "M": range(81, 83), "N": range(83, 85), "O": range(91, 93), "P": range(93, 99),
    "Q": range(0, 1),
}  # fmt: skip
ORDEN_MEDIDAS = ["p10", "p25", "mediana", "media", "p75", "p90"]


def gran_grupo(subgrupo: str) -> str | None:
    """Letra del gran grupo CNO-11 al que pertenece un subgrupo principal ("27" → "C")."""
    return next((g for g, r in GRANDES_GRUPOS_CNO.items() if int(subgrupo) in r), None)


def subgrupos_por_frecuencia(codigos_cno: list[str]) -> list[str]:
    """Un código ISCO puede corresponder a varios CNO: subgrupos del más al menos frecuente."""
    conteo = Counter(c[:2] for c in codigos_cno)
    return sorted(conteo, key=lambda s: (-conteo[s], s))


class Distribucion(BaseModel):
    fuente: str
    periodo: str
    codigo_cno: str
    descripcion: str | None
    medidas: dict[str, float]
    precision_baja: bool


class PuntoTendencia(BaseModel):
    periodo: str
    media: float
    precision_baja: bool


class SalariosOcupacion(BaseModel):
    ocupacion_uri: str
    titulo: str
    isco: str | None
    distribucion: Distribucion | None
    grupo_cno: str | None
    descripcion_grupo: str | None
    tendencia: list[PuntoTendencia]


def _distribucion(db, fuente: str, codigo: str) -> Distribucion | None:
    filas = db.scalars(
        select(EstadisticaSalarial).where(
            EstadisticaSalarial.fuente == fuente, EstadisticaSalarial.codigo_ocupacion == codigo
        )
    ).all()
    if not filas:
        return None
    periodo = max(f.periodo for f in filas)
    ultimas = sorted(
        (f for f in filas if f.periodo == periodo),
        key=lambda f: ORDEN_MEDIDAS.index(f.medida) if f.medida in ORDEN_MEDIDAS else 99,
    )
    return Distribucion(
        fuente=fuente,
        periodo=periodo,
        codigo_cno=codigo,
        descripcion=ultimas[0].descripcion,
        medidas={f.medida: float(f.valor) for f in ultimas},
        precision_baja=any(f.precision_baja for f in ultimas),
    )


@router.get("/salarios", response_model=SalariosOcupacion)
def salarios(
    db: SesionDB, ocupacion: Annotated[str, Query(description="URI ESCO de la ocupación")]
) -> SalariosOcupacion:
    """Ganancia bruta anual (INE) de la ocupación ESCO, vía la correspondencia ISCO → CNO-11.

    Devuelve la distribución más detallada disponible (percentiles del subgrupo CNO-11 en la
    encuesta cuatrienal) y la evolución de la media de su gran grupo en la encuesta anual.
    """
    ocu = db.get(Ocupacion, ocupacion)
    if ocu is None:
        raise HTTPException(status_code=404, detail="Ocupación no encontrada")

    cnos = (
        db.scalars(
            select(CorrespondenciaCnoIsco.cno).where(CorrespondenciaCnoIsco.isco == ocu.grupo_isco)
        ).all()
        if ocu.grupo_isco
        else []
    )
    # El INE no publica los subgrupos con pocas observaciones: se toma el más frecuente
    # que tenga datos y, si ninguno los tiene, el gran grupo.
    subgrupos = subgrupos_por_frecuencia(list(cnos))
    distribucion = next(
        (d for s in subgrupos if (d := _distribucion(db, "INE-EES", s)) is not None), None
    )
    grupo = (
        gran_grupo(distribucion.codigo_cno if distribucion else subgrupos[0]) if subgrupos else None
    )
    if distribucion is None and grupo:
        distribucion = _distribucion(db, "INE-EES", grupo)

    tendencia: list[PuntoTendencia] = []
    descripcion_grupo = None
    if grupo:
        filas = db.scalars(
            select(EstadisticaSalarial)
            .where(
                EstadisticaSalarial.fuente == "INE-EAES",
                EstadisticaSalarial.codigo_ocupacion == grupo,
                EstadisticaSalarial.medida == "media",
            )
            .order_by(EstadisticaSalarial.periodo)
        ).all()
        tendencia = [
            PuntoTendencia(periodo=f.periodo, media=float(f.valor), precision_baja=f.precision_baja)
            for f in filas
        ]
        descripcion_grupo = filas[0].descripcion if filas else None

    return SalariosOcupacion(
        ocupacion_uri=ocu.uri,
        titulo=ocu.titulo,
        isco=ocu.grupo_isco,
        distribucion=distribucion,
        grupo_cno=grupo,
        descripcion_grupo=descripcion_grupo,
        tendencia=tendencia,
    )
