# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Formación oficial relacionada con una ocupación ESCO.

El enlace se hace solo con tablas oficiales: ocupación ESCO → grupo ISCO-08 →
códigos CNO-11 (correspondencia del INE) → especialidades del SEPE que declaran
esa ocupación entre sus ocupaciones relacionadas.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import SesionDB
from gemelo_core.modelos import (
    CorrespondenciaCnoIsco,
    EspecialidadFormativa,
    EspecialidadOcupacion,
    Ocupacion,
)

router = APIRouter()


class EspecialidadSalida(BaseModel):
    codigo: str
    denominacion: str
    familia: str | None
    nivel: int | None
    horas: int | None
    modalidad: str | None
    motivo: str


class FormacionOcupacion(BaseModel):
    ocupacion_uri: str
    titulo: str
    codigos_cno: list[str]
    especialidades: list[EspecialidadSalida]


def agrupar(
    filas: list[tuple[EspecialidadFormativa, str]], limite: int
) -> list[EspecialidadSalida]:
    """Una entrada por especialidad, ordenadas por nº de ocupaciones en común y nivel."""
    por_codigo: dict[str, tuple[EspecialidadFormativa, list[str]]] = {}
    for especialidad, ocupacion in filas:
        por_codigo.setdefault(especialidad.codigo, (especialidad, []))[1].append(ocupacion)

    def orden(item: tuple[EspecialidadFormativa, list[str]]) -> tuple:
        especialidad, ocupaciones = item
        return (-len(ocupaciones), -(especialidad.nivel or 0), especialidad.codigo)

    return [
        EspecialidadSalida(
            codigo=e.codigo,
            denominacion=e.denominacion,
            familia=e.familia,
            nivel=e.nivel,
            horas=e.horas,
            modalidad=e.modalidad,
            motivo="Prepara para: "
            + "; ".join(o.capitalize() for o in sorted(set(ocupaciones)) if not o.isdigit()),
        )
        for e, ocupaciones in sorted(por_codigo.values(), key=orden)[:limite]
    ]


@router.get("/especialidades", response_model=FormacionOcupacion)
def especialidades(
    db: SesionDB,
    ocupacion: Annotated[str, Query(description="URI ESCO de la ocupación")],
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
) -> FormacionOcupacion:
    """Especialidades formativas del SEPE que preparan para la ocupación indicada."""
    ocu = db.get(Ocupacion, ocupacion)
    if ocu is None:
        raise HTTPException(status_code=404, detail="Ocupación no encontrada")

    cnos = sorted(
        db.scalars(
            select(CorrespondenciaCnoIsco.cno).where(CorrespondenciaCnoIsco.isco == ocu.grupo_isco)
        ).all()
    )
    filas = db.execute(
        select(EspecialidadFormativa, EspecialidadOcupacion.titulo)
        .join(EspecialidadOcupacion)
        .where(EspecialidadOcupacion.cno.in_(cnos))
    ).all()

    return FormacionOcupacion(
        ocupacion_uri=ocu.uri,
        titulo=ocu.titulo,
        codigos_cno=cnos,
        especialidades=agrupar([tuple(f) for f in filas], limite),
    )
