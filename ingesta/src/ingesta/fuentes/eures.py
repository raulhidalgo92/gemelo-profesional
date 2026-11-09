# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Ofertas del portal europeo EURES (incluye las publicadas por el SEPE).

Pendiente: EURES no publica una API abierta documentada para terceros. Antes de
implementar se debe confirmar la vía de acceso permitida (convenio, datos
abiertos del SEPE o servicio de búsqueda público) y sus condiciones de uso.
"""

import logging

log = logging.getLogger(__name__)


def ingerir() -> int:
    log.warning("Ingesta EURES todavía no implementada")
    return 0
