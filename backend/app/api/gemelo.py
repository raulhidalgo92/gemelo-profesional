# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Gemelo del usuario: análisis del CV y competencias declaradas."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import delete, select

from app.api.deps import IA, SesionDB, UsuarioActual
from app.servicios import cv
from gemelo_core.ia import ErrorIA
from gemelo_core.modelos import Competencia, Evidencia, Gemelo, GemeloCompetencia

router = APIRouter()


class CompetenciaGemelo(BaseModel):
    uri: str
    titulo: str
    tipo: str | None
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
                origen=fragmento,
                demostrada=demostrado is not None,
            ),
        )
    return list(vistas.values())


@router.post("/cv")
async def subir_cv(
    archivo: UploadFile, usuario: UsuarioActual, s: SesionDB, ia: IA
) -> list[CompetenciaGemelo]:
    """Analiza el CV (PDF o Word) y actualiza las competencias declaradas.
    El archivo se procesa en memoria y no se guarda."""
    if ia is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "ia_no_disponible")
    contenido = await archivo.read(cv.MAX_BYTES + 1)
    try:
        texto = cv.texto_de_archivo(contenido)
        cv.analizar(s, ia, usuario, texto)
    except cv.ErrorCv as e:
        codigo = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if e.codigo == "archivo_grande" else 422
        raise HTTPException(codigo, e.codigo) from e
    except ErrorIA as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "ia_no_disponible") from e
    finally:
        del contenido
    return _competencias(s, usuario.id)


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
