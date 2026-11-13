# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Vectores semánticos (embeddings) de las competencias y ocupaciones ESCO.

Permiten buscar por significado y no solo por texto: es lo que hace posible
relacionar «Angular» con «desarrollar interfaces de usuario». Solo se calculan
los conceptos que todavía no tienen vector, así que la orden se puede relanzar.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select, update

from gemelo_core.db import sesion
from gemelo_core.ia import TAREA_DOCUMENTO, ClienteIA, ErrorIA, cliente_ia
from gemelo_core.modelos import Competencia, Ocupacion
from ingesta.fuentes._util import lotes

log = logging.getLogger(__name__)

TAM_LOTE = 50
HILOS = 8
MAX_CARACTERES = 2000


def texto_concepto(titulo: str, alternativos: str | None, descripcion: str | None) -> str:
    """Texto que representa un concepto ESCO: título, sinónimos y descripción."""
    partes = [titulo.strip()]
    if alternativos:
        sinonimos = [a.strip() for a in alternativos.splitlines() if a.strip()][:8]
        if sinonimos:
            partes.append("También: " + ", ".join(sinonimos) + ".")
    if descripcion:
        partes.append(descripcion.strip())
    return "\n".join(partes)[:MAX_CARACTERES]


def con_reintentos(funcion, *args, intentos: int = 5):
    for intento in range(1, intentos + 1):
        try:
            return funcion(*args)
        except ErrorIA as e:
            if intento == intentos:
                raise
            log.warning("Fallo de la API (%s); reintento %d", str(e)[:120], intento)
            time.sleep(2**intento)


def vectorizar(cliente: ClienteIA, textos: list[str]) -> list[list[float]]:
    """Calcula embeddings por lotes; si el modelo no admite lotes, de uno en uno en paralelo."""
    try:
        return con_reintentos(lambda t: cliente.embeddings(t, tarea=TAREA_DOCUMENTO), textos)
    except ErrorIA:
        if len(textos) == 1:
            raise
        log.info("El modelo no acepta lotes de %d textos; se envían de uno en uno", len(textos))
    with ThreadPoolExecutor(HILOS) as hilos:
        return list(
            hilos.map(
                lambda t: con_reintentos(
                    lambda x: cliente.embeddings([x], tarea=TAREA_DOCUMENTO)[0], t
                ),
                textos,
            )
        )


def _procesar(modelo, cliente: ClienteIA, limite: int | None) -> int:
    with sesion() as s:
        consulta = select(
            modelo.uri, modelo.titulo, modelo.titulos_alternativos, modelo.descripcion
        ).where(modelo.embedding.is_(None))
        if limite:
            consulta = consulta.limit(limite)
        pendientes = s.execute(consulta).all()

    log.info("%s: %d conceptos sin vector", modelo.__tablename__, len(pendientes))
    hechos = 0
    for lote in lotes(pendientes, TAM_LOTE):
        vectores = vectorizar(cliente, [texto_concepto(f[1], f[2], f[3]) for f in lote])
        with sesion() as s:
            s.execute(
                update(modelo),
                [{"uri": f[0], "embedding": v} for f, v in zip(lote, vectores, strict=True)],
            )
        hechos += len(lote)
        log.info("%s: %d/%d", modelo.__tablename__, hechos, len(pendientes))
    return hechos


def cargar(limite: int | None = None) -> None:
    cliente = cliente_ia()
    total = sum(_procesar(m, cliente, limite) for m in (Competencia, Ocupacion))
    log.info("Embeddings completados: %d conceptos", total)
