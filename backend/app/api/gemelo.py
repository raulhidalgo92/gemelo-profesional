# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Gemelo del usuario: análisis del CV, trayectoria y competencias declaradas."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select

from app.api.deps import IA, SesionDB, UsuarioActual
from app.servicios import cv
from gemelo_core.ia import ErrorIA
from gemelo_core.modelos import Competencia, Evidencia, Gemelo, GemeloCompetencia
from gemelo_core.trayectoria import PerfilCv

router = APIRouter()


class CompetenciaGemelo(BaseModel):
    uri: str
    titulo: str
    tipo: str | None
    # Nivel de reutilización ESCO: transversal, cross-sector, sector-specific u occupation-specific
    alcance: str | None
    # Fragmento del CV del que se dedujo (explicación)
    origen: str | None
    demostrada: bool


def _competencias(s: SesionDB, usuario_id) -> list[CompetenciaGemelo]:
    filas = s.execute(
        select(Competencia, GemeloCompetencia.nivel_demostrado, Evidencia.fragmento)
        .join(GemeloCompetencia, GemeloCompetencia.competencia_uri == Competencia.uri)
        .join(Gemelo, Gemelo.id == GemeloCompetencia.gemelo_id)
        .outerjoin(
            Evidencia,
            (Evidencia.gemelo_id == Gemelo.id)
            & (Evidencia.competencia_uri == Competencia.uri)
            & (Evidencia.origen == "cv"),
        )
        .where(Gemelo.usuario_id == usuario_id)
        .order_by(Competencia.titulo)
    ).all()
    vistas: dict[str, CompetenciaGemelo] = {}
    for comp, demostrado, fragmento in filas:
        vistas.setdefault(
            comp.uri,
            CompetenciaGemelo(
                uri=comp.uri,
                titulo=comp.titulo,
                tipo=comp.tipo,
                alcance=comp.nivel_reutilizacion,
                origen=fragmento,
                demostrada=demostrado is not None,
            ),
        )
    return list(vistas.values())


class CompetenciaCv(BaseModel):
    uri: Annotated[str, Field(max_length=255)]
    titulo: str = ""
    # Término del CV del que se dedujo (explicación)
    termino: Annotated[str, Field(max_length=500)]
    similitud: Annotated[float, Field(ge=0, le=1)]
    # No estaba en el gemelo antes de este CV
    nueva: bool = False


class AnalisisCvSalida(BaseModel):
    perfil: PerfilCv
    competencias: list[CompetenciaCv]
    # Solo venían del CV anterior y el nuevo no las trae: el usuario decide si se quedan
    ya_no: list[CompetenciaGemelo]
    trayectoria_cambia: bool


class AplicarCvEntrada(BaseModel):
    perfil: PerfilCv
    competencias: Annotated[list[CompetenciaCv], Field(max_length=60)]
    conservar: Annotated[list[str], Field(max_length=60)] = []


@router.post("/cv/analizar")
async def analizar_cv(
    archivo: UploadFile, usuario: UsuarioActual, s: SesionDB, ia: IA
) -> AnalisisCvSalida:
    """Analiza el CV (PDF o Word) y devuelve los cambios sin guardar nada.
    El archivo se procesa en memoria y no se guarda."""
    if ia is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "ia_no_disponible")
    contenido = await archivo.read(cv.MAX_BYTES + 1)
    try:
        perfil, detectadas = cv.analizar(s, ia, usuario, cv.texto_de_archivo(contenido))
    except cv.ErrorCv as e:
        codigo = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if e.codigo == "archivo_grande" else 422
        raise HTTPException(codigo, e.codigo) from e
    except ErrorIA as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "ia_no_disponible") from e
    finally:
        del contenido

    gemelo = s.scalar(select(Gemelo).where(Gemelo.usuario_id == usuario.id))
    actuales = _competencias(s, usuario.id)
    previas = {c.uri for c in actuales}
    ya_no = cv.solo_del_cv(s, gemelo.id) - {c.uri for c in detectadas} if gemelo else set()
    return AnalisisCvSalida(
        perfil=perfil,
        competencias=[
            CompetenciaCv(
                uri=c.uri,
                titulo=c.titulo,
                termino=c.termino,
                similitud=c.similitud,
                nueva=c.uri not in previas,
            )
            for c in detectadas
        ],
        ya_no=[c for c in actuales if c.uri in ya_no],
        trayectoria_cambia=cv.trayectoria_cambia(gemelo, perfil),
    )


@router.post("/cv/aplicar")
def aplicar_cv(
    entrada: AplicarCvEntrada, usuario: UsuarioActual, s: SesionDB
) -> list[CompetenciaGemelo]:
    """Guarda lo que el usuario ha confirmado tras revisar el análisis del CV."""
    cv.aplicar(
        s,
        usuario,
        entrada.perfil,
        [cv.CompetenciaCv(c.uri, c.termino, c.similitud) for c in entrada.competencias],
        set(entrada.conservar),
    )
    return _competencias(s, usuario.id)


class GemeloSalida(BaseModel):
    # Sin perfil: todavía no ha subido un CV con el que extraer la trayectoria
    perfil: PerfilCv | None
    actualizado_en: datetime | None


@router.get("")
def gemelo(usuario: UsuarioActual, s: SesionDB) -> GemeloSalida:
    g = s.scalar(select(Gemelo).where(Gemelo.usuario_id == usuario.id))
    if g is None or g.trayectoria is None:
        return GemeloSalida(perfil=None, actualizado_en=None)
    perfil = PerfilCv.model_validate({**g.trayectoria, "nivel_ingles": g.nivel_ingles})
    return GemeloSalida(perfil=perfil, actualizado_en=g.actualizado_en)


@router.get("/competencias")
def competencias(usuario: UsuarioActual, s: SesionDB) -> list[CompetenciaGemelo]:
    return _competencias(s, usuario.id)


@router.delete("/competencias", status_code=status.HTTP_204_NO_CONTENT)
def quitar_competencia(uri: str = Query(), *, usuario: UsuarioActual, s: SesionDB) -> None:
    """El usuario corrige su gemelo quitando una competencia que no reconoce."""
    gemelo_id = s.scalar(select(Gemelo.id).where(Gemelo.usuario_id == usuario.id))
    s.execute(
        delete(Evidencia).where(Evidencia.gemelo_id == gemelo_id, Evidencia.competencia_uri == uri)
    )
    s.execute(
        delete(GemeloCompetencia).where(
            GemeloCompetencia.gemelo_id == gemelo_id, GemeloCompetencia.competencia_uri == uri
        )
    )
    s.commit()
