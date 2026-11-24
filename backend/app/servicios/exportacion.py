# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Copia de los datos del usuario en un formato legible y reutilizable (RGPD, art. 20).

Incluye todo lo que la aplicación guarda sobre la persona salvo los secretos: ni el
resumen de la contraseña ni los de las sesiones o códigos de activación.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from gemelo_core.modelos import Competencia, Entrevista, Evidencia, GemeloCompetencia, Usuario


def _fecha(valor: datetime | None) -> str | None:
    return valor.isoformat() if valor else None


def exportar(s: Session, usuario: Usuario) -> dict:
    datos: dict = {
        "exportado_en": _fecha(datetime.now().astimezone()),
        "cuenta": {
            "nombre": usuario.nombre,
            "email": usuario.email,
            "avatar": usuario.avatar,
            "creada_en": _fecha(usuario.creado_en),
            "verificada_en": _fecha(usuario.verificado_en),
            "consentimiento": {
                "aceptado_en": _fecha(usuario.consentimiento_en),
                "version": usuario.consentimiento_version,
            },
        },
        "gemelo": None,
    }
    gemelo = usuario.gemelo
    if gemelo is None:
        return datos

    competencias = s.execute(
        select(GemeloCompetencia, Competencia.titulo)
        .join(Competencia, Competencia.uri == GemeloCompetencia.competencia_uri)
        .where(GemeloCompetencia.gemelo_id == gemelo.id)
        .order_by(Competencia.titulo)
    ).all()
    evidencias = s.scalars(
        select(Evidencia).where(Evidencia.gemelo_id == gemelo.id).order_by(Evidencia.creado_en)
    ).all()
    entrevistas = s.scalars(
        select(Entrevista).where(Entrevista.gemelo_id == gemelo.id).order_by(Entrevista.creado_en)
    ).all()

    datos["gemelo"] = {
        "actualizado_en": _fecha(gemelo.actualizado_en),
        "trayectoria": gemelo.trayectoria,
        "nivel_ingles": gemelo.nivel_ingles,
        "competencias": [
            {
                "uri": c.competencia_uri,
                "titulo": titulo,
                "nivel_declarado": c.nivel_declarado,
                "nivel_demostrado": c.nivel_demostrado,
            }
            for c, titulo in competencias
        ],
        "evidencias": [
            {
                "competencia_uri": e.competencia_uri,
                "origen": e.origen,
                "fragmento": e.fragmento,
                "puntuacion": e.puntuacion,
                "explicacion": e.explicacion,
                "creada_en": _fecha(e.creado_en),
            }
            for e in evidencias
        ],
        "entrevistas": [
            {
                "modo": e.modo,
                "turnos": e.turnos,
                "nota_global": e.nota_global,
                "nivel_ingles_estimado": e.nivel_ingles_estimado,
                "creada_en": _fecha(e.creado_en),
            }
            for e in entrevistas
        ],
    }
    return datos
