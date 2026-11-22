# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Modelo de datos: mercado laboral, formación y usuario (gemelo)."""

from gemelo_core.modelos.base import Base
from gemelo_core.modelos.formacion import (
    Curso,
    EspecialidadFormativa,
    EspecialidadOcupacion,
    ItinerarioFormativo,
)
from gemelo_core.modelos.mercado import (
    Competencia,
    CorrespondenciaCnoIsco,
    EstadisticaSalarial,
    MapeoEscoOnet,
    Ocupacion,
    OcupacionCompetencia,
    OcupacionOnet,
    Oferta,
    OfertaCompetencia,
    TransicionOnet,
)
from gemelo_core.modelos.usuario import (
    CodigoVerificacion,
    Entrevista,
    Evidencia,
    Gemelo,
    GemeloCompetencia,
    SesionUsuario,
    Usuario,
)

__all__ = [
    "Base",
    "CodigoVerificacion",
    "Competencia",
    "CorrespondenciaCnoIsco",
    "Curso",
    "Entrevista",
    "EspecialidadFormativa",
    "EspecialidadOcupacion",
    "EstadisticaSalarial",
    "Evidencia",
    "Gemelo",
    "GemeloCompetencia",
    "ItinerarioFormativo",
    "MapeoEscoOnet",
    "Ocupacion",
    "OcupacionCompetencia",
    "OcupacionOnet",
    "Oferta",
    "OfertaCompetencia",
    "TransicionOnet",
    "SesionUsuario",
    "Usuario",
]
