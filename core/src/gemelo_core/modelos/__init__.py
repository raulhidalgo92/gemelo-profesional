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
    Entrevista,
    Evidencia,
    Gemelo,
    GemeloCompetencia,
    Usuario,
)

__all__ = [
    "Base",
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
    "Usuario",
]
