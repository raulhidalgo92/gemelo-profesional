# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Guardado común de ofertas de cualquier fuente.

Cada fuente publica la lista completa de ofertas vigentes, así que en cada carga:
1. se eliminan los datos de contacto del texto (RGPD: no los necesitamos),
2. se insertan o actualizan las ofertas,
3. se borran las de esa fuente que ya no aparecen (han caducado o se han retirado).
"""

import html
import logging
import re

from gemelo_core.db import sesion
from gemelo_core.modelos import Oferta
from gemelo_core.seudonimizacion import eliminar_datos_contacto
from ingesta.fuentes._util import sustituir_vigentes

log = logging.getLogger(__name__)


def texto_plano(contenido: str | None) -> str:
    """Quita etiquetas HTML y espacios sobrantes."""
    sin_etiquetas = re.sub(r"<[^>]+>", " ", contenido or "")
    return re.sub(r"\s+", " ", html.unescape(sin_etiquetas)).strip()


def limpiar(oferta: dict) -> dict:
    for campo in ("titulo", "texto"):
        if oferta.get(campo):
            oferta[campo] = eliminar_datos_contacto(oferta[campo])
    return oferta


def guardar(fuente: str, ofertas: list[dict]) -> int:
    """Sustituye las ofertas guardadas de `fuente` por las recibidas."""
    if not ofertas:  # probablemente un fallo de la fuente: no borrar lo que ya hay
        log.warning("%s: no se ha recibido ninguna oferta, se conservan las anteriores", fuente)
        return 0
    ofertas = [limpiar(o) for o in ofertas]
    with sesion() as s:
        vigentes, retiradas = sustituir_vigentes(s, Oferta, fuente, ofertas)
        s.commit()
    log.info("%s: %d ofertas vigentes, %d retiradas", fuente, vigentes, retiradas)
    return vigentes
