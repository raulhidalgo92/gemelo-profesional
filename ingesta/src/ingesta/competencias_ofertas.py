# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Extracción de competencias ESCO de las ofertas que aún no se han procesado.

Se procesan primero las más recientes y como mucho `limite` en cada ejecución, para
controlar el gasto. Una oferta que falla se queda pendiente y se reintenta la próxima vez.
Al terminar se registran los tokens consumidos para conocer el coste real.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import delete, func, insert, select, update

from gemelo_core.db import sesion
from gemelo_core.extraccion import asociar_a_esco, ocupacion_probable, proponer_terminos
from gemelo_core.ia import ClienteIA, ErrorIA, cliente_ia
from gemelo_core.modelos import Oferta, OfertaCompetencia
from ingesta.fuentes.embeddings import con_reintentos

log = logging.getLogger(__name__)

HILOS = 8
UMBRAL_OCUPACION = 0.7


def pendientes(limite: int) -> list[tuple[int, str, str]]:
    with sesion() as s:
        return [
            tuple(f)
            for f in s.execute(
                select(Oferta.id, Oferta.titulo, Oferta.texto)
                .where(Oferta.procesada_en.is_(None))
                .order_by(Oferta.publicada_en.desc().nulls_last(), Oferta.id)
                .limit(limite)
            )
        ]


def procesar_oferta(ia: ClienteIA, oferta_id: int, titulo: str, texto: str | None) -> int:
    """Extrae y guarda las competencias de una oferta. Devuelve cuántas se han guardado."""
    terminos = con_reintentos(proponer_terminos, ia, f"{titulo}\n\n{texto or ''}")
    with sesion() as s:
        detectadas = con_reintentos(asociar_a_esco, s, ia, terminos, titulo)
        ocupacion = con_reintentos(ocupacion_probable, s, ia, titulo)
        s.execute(delete(OfertaCompetencia).where(OfertaCompetencia.oferta_id == oferta_id))
        if detectadas:
            s.execute(
                insert(OfertaCompetencia),
                [
                    {
                        "oferta_id": oferta_id,
                        "competencia_uri": c.uri,
                        "confianza": c.similitud,
                        "termino": c.termino[:255],
                    }
                    for c in detectadas
                ],
            )
        s.execute(
            update(Oferta)
            .where(Oferta.id == oferta_id)
            .values(
                procesada_en=func.now(),
                ocupacion_uri=(
                    ocupacion.uri if ocupacion and ocupacion.similitud >= UMBRAL_OCUPACION else None
                ),
            )
        )
        s.commit()
    return len(detectadas)


def procesar(limite: int) -> int:
    ia = cliente_ia()
    ofertas = pendientes(limite)
    log.info("Extracción de competencias: %d ofertas pendientes (límite %d)", len(ofertas), limite)

    def tarea(oferta: tuple[int, str, str]) -> int | None:
        try:
            return procesar_oferta(ia, *oferta)
        except ErrorIA as e:  # se queda pendiente para la próxima ejecución
            log.warning("Oferta %d sin procesar: %s", oferta[0], str(e)[:150])
            return None

    with ThreadPoolExecutor(HILOS) as hilos:
        resultados = list(hilos.map(tarea, ofertas))

    hechas = [r for r in resultados if r is not None]
    log.info(
        "Procesadas %d ofertas, %d competencias, %d fallidas. Tokens: %s",
        len(hechas),
        sum(hechas),
        len(resultados) - len(hechas),
        dict(ia.uso),
    )
    return len(hechas)
