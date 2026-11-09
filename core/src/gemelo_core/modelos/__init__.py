# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Modelo de datos. Se divide en dos dominios: mercado laboral y usuario (gemelo)."""

from gemelo_core.modelos.base import Base
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
    "Entrevista",
    "EstadisticaSalarial",
    "Evidencia",
    "Gemelo",
    "GemeloCompetencia",
    "MapeoEscoOnet",
    "Ocupacion",
    "OcupacionCompetencia",
    "OcupacionOnet",
    "Oferta",
    "OfertaCompetencia",
    "TransicionOnet",
    "Usuario",
]
