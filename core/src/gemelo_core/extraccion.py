# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Extracción de competencias ESCO de un texto (ofertas de empleo).

Tres pasos, siguiendo la estrategia de Clavié y Soulié (2023):
1. Un modelo de lenguaje ligero propone las competencias como términos breves.
2. Para cada término se buscan por significado las competencias ESCO más parecidas.
3. El mismo modelo elige, para cada término, la candidata correcta o ninguna.

Un umbral de similitud no basta: las similitudes de buenas y malas parejas se solapan
(«puntualidad» se parece más a «garantizar el horario de los trenes» que «español» a
«español»). Se conserva el término original para explicar cada competencia detectada.

La ocupación de la oferta se obtiene igual: el modelo nombra el puesto en español, se
buscan las ocupaciones ESCO más parecidas y el modelo elige una o ninguna.
"""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from gemelo_core.ia import TAREA_CONSULTA, ClienteIA, ErrorIA
from gemelo_core.modelos import Competencia, Ocupacion

_PROMPTS = Path(__file__).parent / "prompts"
PROMPT_TERMINOS = (_PROMPTS / "extraccion_competencias.md").read_text("utf-8")
PROMPT_ELECCION = (_PROMPTS / "eleccion_competencias.md").read_text("utf-8")
PROMPT_PUESTO = (_PROMPTS / "puesto_oferta.md").read_text("utf-8")
PROMPT_OCUPACION = (_PROMPTS / "eleccion_ocupacion.md").read_text("utf-8")
VERSION_PROMPTS = "2"

MAX_CARACTERES = 4000
MAX_TERMINOS = 20
K_CANDIDATAS = 5
SIMILITUD_MINIMA = 0.55  # por debajo, la candidata no tiene relación y no se envía


class RespuestaTerminos(BaseModel):
    competencias: list[str]


class Eleccion(BaseModel):
    termino: int | str  # el número del término (a veces el modelo devuelve el texto)
    candidata: int | None


class RespuestaEleccion(BaseModel):
    elecciones: list[Eleccion]


class RespuestaPuesto(BaseModel):
    puesto: str | None


class RespuestaOcupacion(BaseModel):
    candidata: int | None


@dataclass(frozen=True)
class Candidata:
    uri: str
    titulo: str
    similitud: float


@dataclass(frozen=True)
class CompetenciaDetectada:
    uri: str
    titulo: str
    termino: str
    similitud: float


def _pedir_json[T: BaseModel](
    ia: ClienteIA, mensajes: list[dict[str, str]], esquema: type[T], modelo: str | None
) -> T:
    """Llama al modelo y valida la respuesta; si no es válida, un reintento con el error."""
    for intento in range(2):
        datos = ia.completar_json(mensajes, modelo=modelo or ia.cfg.llm_modelo_ligero)
        try:
            return esquema.model_validate(datos)
        except ValidationError as e:
            if intento == 1:
                raise ErrorIA(f"Respuesta con formato incorrecto: {e}") from e
            mensajes = [*mensajes, {"role": "user", "content": f"Formato incorrecto: {e}"}]
    raise AssertionError("inalcanzable")


def proponer_terminos(ia: ClienteIA, texto: str, modelo: str | None = None) -> list[str]:
    """Paso 1: el modelo de lenguaje propone las competencias del texto."""
    mensajes = [
        {"role": "system", "content": PROMPT_TERMINOS},
        {"role": "user", "content": f"Oferta:\n{texto[:MAX_CARACTERES]}"},
    ]
    terminos = _pedir_json(ia, mensajes, RespuestaTerminos, modelo).competencias
    unicos = dict.fromkeys(t.strip() for t in terminos if t and t.strip())
    return list(unicos)[:MAX_TERMINOS]


def candidatas(s: Session, modelo, vector: list[float], k: int = K_CANDIDATAS) -> list[Candidata]:
    """Paso 2: los `k` conceptos ESCO (competencias u ocupaciones) más cercanos a un vector."""
    distancia = modelo.embedding.cosine_distance(vector)
    filas = s.execute(
        select(modelo.uri, modelo.titulo, distancia)
        .where(modelo.embedding.is_not(None))
        .order_by(distancia)
        .limit(k)
    ).all()
    return [Candidata(uri, titulo, round(1 - d, 4)) for uri, titulo, d in filas]


def texto_eleccion(contexto: str, terminos: list[str], opciones: list[list[Candidata]]) -> str:
    lineas = [f"Oferta: {contexto}", "", "Términos y candidatas:"]
    for i, (termino, cands) in enumerate(zip(terminos, opciones, strict=True), start=1):
        lineas.append(f"{i}. «{termino}»")
        lineas += [f"   {j}) {c.titulo}" for j, c in enumerate(cands, start=1)]
    return "\n".join(lineas)


def elegir(
    ia: ClienteIA,
    contexto: str,
    terminos: list[str],
    opciones: list[list[Candidata]],
    modelo: str | None = None,
) -> list[CompetenciaDetectada]:
    """Paso 3: el modelo elige la candidata correcta de cada término (o ninguna)."""
    mensajes = [
        {"role": "system", "content": PROMPT_ELECCION},
        {"role": "user", "content": texto_eleccion(contexto, terminos, opciones)},
    ]
    respuesta = _pedir_json(ia, mensajes, RespuestaEleccion, modelo)

    posiciones = {t.casefold(): i for i, t in enumerate(terminos, start=1)}
    detectadas: dict[str, CompetenciaDetectada] = {}
    for e in respuesta.elecciones:
        n = e.termino if isinstance(e.termino, int) else posiciones.get(e.termino.casefold(), 0)
        if e.candidata is None or not 1 <= n <= len(terminos):
            continue
        cands = opciones[n - 1]
        if not 1 <= e.candidata <= len(cands):
            continue  # índice inventado por el modelo: se ignora
        c = cands[e.candidata - 1]
        if c.uri not in detectadas or c.similitud > detectadas[c.uri].similitud:
            detectadas[c.uri] = CompetenciaDetectada(c.uri, c.titulo, terminos[n - 1], c.similitud)
    return sorted(detectadas.values(), key=lambda c: -c.similitud)


def asociar_a_esco(
    s: Session, ia: ClienteIA, terminos: list[str], contexto: str
) -> list[CompetenciaDetectada]:
    """Pasos 2 y 3 para una lista de términos. `contexto` es, por ejemplo, el título."""
    if not terminos:
        return []
    vectores = ia.embeddings(terminos, tarea=TAREA_CONSULTA)
    con_candidatas = []
    for termino, vector in zip(terminos, vectores, strict=True):
        cands = [c for c in candidatas(s, Competencia, vector) if c.similitud >= SIMILITUD_MINIMA]
        if cands:
            con_candidatas.append((termino, cands))
    if not con_candidatas:
        return []
    return elegir(ia, contexto, [t for t, _ in con_candidatas], [c for _, c in con_candidatas])


def nombrar_puesto(ia: ClienteIA, titulo: str, modelo: str | None = None) -> str | None:
    """Nombre en español de la ocupación de una oferta («FUSTERS/ES» → «carpintero»)."""
    mensajes = [
        {"role": "system", "content": PROMPT_PUESTO},
        {"role": "user", "content": f"Título: {titulo}"},
    ]
    puesto = _pedir_json(ia, mensajes, RespuestaPuesto, modelo).puesto
    return puesto.strip() if puesto and puesto.strip() else None


def elegir_ocupacion(
    ia: ClienteIA, titulo: str, puesto: str, opciones: list[Candidata], modelo: str | None = None
) -> Candidata | None:
    """El modelo elige la ocupación ESCO del puesto entre las candidatas (o ninguna)."""
    lineas = [f"Oferta: {titulo}", f"Puesto: {puesto}", "", "Candidatas:"]
    lineas += [f"{i}) {c.titulo}" for i, c in enumerate(opciones, start=1)]
    mensajes = [
        {"role": "system", "content": PROMPT_OCUPACION},
        {"role": "user", "content": "\n".join(lineas)},
    ]
    n = _pedir_json(ia, mensajes, RespuestaOcupacion, modelo).candidata
    return opciones[n - 1] if n is not None and 1 <= n <= len(opciones) else None


def ocupacion_probable(s: Session, ia: ClienteIA, titulo: str) -> Candidata | None:
    """Ocupación ESCO de una oferta: se nombra el puesto, se buscan candidatas y se elige.

    Buscar directamente por el título falla con los títulos en catalán: «FUSTERS/ES»
    queda más cerca de «cartero» que de «carpintero».
    """
    puesto = nombrar_puesto(ia, titulo)
    if puesto is None:
        return None
    [vector] = ia.embeddings([puesto], tarea=TAREA_CONSULTA)
    opciones = [c for c in candidatas(s, Ocupacion, vector) if c.similitud >= SIMILITUD_MINIMA]
    return elegir_ocupacion(ia, titulo, puesto, opciones) if opciones else None


def extraer_competencias(
    s: Session, ia: ClienteIA, titulo: str, texto: str
) -> list[CompetenciaDetectada]:
    """Competencias ESCO de una oferta (los tres pasos seguidos)."""
    terminos = proponer_terminos(ia, f"{titulo}\n\n{texto}")
    return asociar_a_esco(s, ia, terminos, contexto=titulo)
