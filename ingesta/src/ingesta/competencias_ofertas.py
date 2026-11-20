# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Extracción de competencias ESCO de las ofertas que aún no se han procesado.

Se procesan primero las más recientes y como mucho `limite` en cada ejecución, para
controlar el gasto. Una oferta que falla se queda pendiente y se reintenta la próxima vez.
Al terminar se registran los tokens consumidos para conocer el coste real.

`recalcular_ocupaciones` vuelve a estimar solo la ocupación de las ofertas ya procesadas,
por ejemplo tras cambiar el procedimiento, sin repetir la extracción de competencias.
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
                ocupacion_uri=ocupacion.uri if ocupacion else None,
            )
        )
        s.commit()
    return len(detectadas)


def _en_paralelo(ia: ClienteIA, funcion, ofertas: list[tuple]) -> list:
    """Aplica `funcion(ia, *oferta)` en varios hilos; None en las ofertas que fallan."""

    def tarea(oferta: tuple):
        try:
            return funcion(ia, *oferta)
        except ErrorIA as e:  # se queda pendiente para la próxima ejecución
            log.warning("Oferta %d sin procesar: %s", oferta[0], str(e)[:150])
            return None

    with ThreadPoolExecutor(HILOS) as hilos:
        return list(hilos.map(tarea, ofertas))


def procesar(limite: int) -> int:
    ia = cliente_ia()
    ofertas = pendientes(limite)
    log.info("Extracción de competencias: %d ofertas pendientes (límite %d)", len(ofertas), limite)
    resultados = _en_paralelo(ia, procesar_oferta, ofertas)

    hechas = [r for r in resultados if r is not None]
    log.info(
        "Procesadas %d ofertas, %d competencias, %d fallidas. Tokens: %s",
        len(hechas),
        sum(hechas),
        len(resultados) - len(hechas),
        dict(ia.uso),
    )
    return len(hechas)


def recalcular_ocupacion(ia: ClienteIA, oferta_id: int, titulo: str) -> bool:
    """Vuelve a estimar la ocupación de una oferta. Devuelve si se ha encontrado."""
    with sesion() as s:
        ocupacion = con_reintentos(ocupacion_probable, s, ia, titulo)
        s.execute(
            update(Oferta)
            .where(Oferta.id == oferta_id)
            .values(ocupacion_uri=ocupacion.uri if ocupacion else None)
        )
        s.commit()
    return ocupacion is not None


def recalcular_ocupaciones(limite: int | None = None, solo_sin_ocupacion: bool = False) -> int:
    ia = cliente_ia()
    with sesion() as s:
        consulta = select(Oferta.id, Oferta.titulo).where(Oferta.procesada_en.is_not(None))
        if solo_sin_ocupacion:
            consulta = consulta.where(Oferta.ocupacion_uri.is_(None))
        ofertas = [tuple(f) for f in s.execute(consulta.order_by(Oferta.id).limit(limite))]
    log.info("Recalculando la ocupación de %d ofertas", len(ofertas))
    resultados = _en_paralelo(ia, recalcular_ocupacion, ofertas)
    log.info(
        "Con ocupación: %d. Sin ocupación: %d. Fallidas: %d. Tokens: %s",
        resultados.count(True),
        resultados.count(False),
        resultados.count(None),
        dict(ia.uso),
    )
    return resultados.count(True)
