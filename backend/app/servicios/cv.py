# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Análisis del currículum: texto → seudonimización → trayectoria y competencias ESCO.

Dos pasos: `analizar` extrae sin guardar nada y `aplicar` guarda lo que el usuario
confirma tras revisar los cambios.

RGPD: el archivo se procesa en memoria y nunca se guarda. Antes de enviar el texto al
modelo de lenguaje se sustituyen los datos identificativos por marcadores, y del CV solo
se conservan la trayectoria (sin empresas ni centros), las competencias y el término del
que se dedujo cada una.
"""

import io
import zipfile
from dataclasses import dataclass

from docx import Document
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import delete, exists, select, update
from sqlalchemy.orm import Session

from gemelo_core.extraccion import CompetenciaDetectada, asociar_a_esco, proponer_terminos
from gemelo_core.ia import ClienteIA
from gemelo_core.modelos import Competencia, Evidencia, Gemelo, GemeloCompetencia, Usuario
from gemelo_core.seudonimizacion import seudonimizar
from gemelo_core.trayectoria import PerfilCv, extraer_perfil

MAX_BYTES = 5 * 1024 * 1024
MIN_CARACTERES = 200
NIVEL_DECLARADO = 0.5  # declarada en el CV, sin evidencia todavía


class ErrorCv(Exception):
    def __init__(self, codigo: str):
        super().__init__(codigo)
        self.codigo = codigo


@dataclass(frozen=True)
class CompetenciaCv:
    """Competencia del CV que el usuario confirma (sin título: se toma de ESCO)."""

    uri: str
    termino: str
    similitud: float


def texto_de_archivo(contenido: bytes) -> str:
    """Texto de un PDF o de un Word (.docx), reconocidos por su contenido, no por el nombre."""
    if len(contenido) > MAX_BYTES:
        raise ErrorCv("archivo_grande")
    if contenido.startswith(b"%PDF"):
        try:
            paginas = PdfReader(io.BytesIO(contenido)).pages
            texto = "\n".join(p.extract_text() or "" for p in paginas)
        except PdfReadError as e:
            raise ErrorCv("archivo_ilegible") from e
    elif contenido.startswith(b"PK"):
        try:
            doc = Document(io.BytesIO(contenido))
        except (zipfile.BadZipFile, KeyError, ValueError) as e:
            raise ErrorCv("archivo_ilegible") from e
        celdas = [c.text for t in doc.tables for fila in t.rows for c in fila.cells]
        texto = "\n".join([p.text for p in doc.paragraphs] + celdas)
    else:
        raise ErrorCv("formato_no_admitido")
    texto = "\n".join(linea.strip() for linea in texto.splitlines() if linea.strip())
    if len(texto) < MIN_CARACTERES:
        raise ErrorCv("sin_texto")  # p. ej., un PDF escaneado como imagen
    return texto


def nombres_a_ocultar(texto: str, nombre: str) -> list[str]:
    """El nombre de la cuenta y la cabecera del CV, que casi siempre es nombre y apellidos."""
    nombres = [nombre] if nombre else []
    cabecera = texto.splitlines()[0].strip() if texto else ""
    if 1 < len(cabecera.split()) <= 5 and not any(ch.isdigit() or ch == "@" for ch in cabecera):
        nombres.insert(0, cabecera)  # primero el nombre completo
    return nombres


def analizar(
    s: Session, ia: ClienteIA, usuario: Usuario, texto: str
) -> tuple[PerfilCv, list[CompetenciaDetectada]]:
    """Perfil y competencias ESCO del CV, sin guardar nada: el usuario los revisa antes."""
    seudo = seudonimizar(texto, nombres=nombres_a_ocultar(texto, usuario.nombre))
    terminos = proponer_terminos(ia, seudo.texto, cv=True)
    detectadas = asociar_a_esco(s, ia, terminos, contexto="currículum de un profesional")
    return extraer_perfil(ia, seudo.texto), detectadas


def gemelo_de(s: Session, usuario: Usuario) -> Gemelo:
    gemelo = s.scalar(select(Gemelo).where(Gemelo.usuario_id == usuario.id))
    if gemelo is None:
        gemelo = Gemelo(usuario_id=usuario.id)
        s.add(gemelo)
        s.flush()
    return gemelo


def solo_del_cv(s: Session, gemelo_id: int) -> set[str]:
    """Competencias que están en el gemelo únicamente porque las traía el CV anterior."""
    otra_evidencia = exists().where(
        Evidencia.gemelo_id == gemelo_id,
        Evidencia.competencia_uri == GemeloCompetencia.competencia_uri,
        Evidencia.origen != "cv",
    )
    return set(
        s.scalars(
            select(GemeloCompetencia.competencia_uri).where(
                GemeloCompetencia.gemelo_id == gemelo_id,
                GemeloCompetencia.nivel_demostrado.is_(None),
                ~otra_evidencia,
            )
        )
    )


def aplicar(
    s: Session,
    usuario: Usuario,
    perfil: PerfilCv,
    competencias: list[CompetenciaCv],
    conservar: set[str],
) -> None:
    """Sustituye lo que venía del CV anterior por lo que el usuario ha confirmado.

    Lo demostrado o añadido por el usuario no se toca. De lo que solo venía del CV
    anterior, se conserva lo que el usuario indica en `conservar`.
    """
    gemelo = gemelo_de(s, usuario)
    unicas = {c.uri: c for c in competencias}
    validas = set(s.scalars(select(Competencia.uri).where(Competencia.uri.in_(unicas))))

    # Lo que el usuario conserva queda confirmado: no se vuelve a preguntar por ello
    s.execute(
        update(Evidencia)
        .where(
            Evidencia.gemelo_id == gemelo.id,
            Evidencia.origen == "cv",
            Evidencia.competencia_uri.in_(conservar - validas),
        )
        .values(origen="conservada")
    )
    s.execute(delete(Evidencia).where(Evidencia.gemelo_id == gemelo.id, Evidencia.origen == "cv"))
    sin_respaldo = ~exists().where(
        Evidencia.gemelo_id == gemelo.id,
        Evidencia.competencia_uri == GemeloCompetencia.competencia_uri,
    )
    s.execute(
        delete(GemeloCompetencia).where(
            GemeloCompetencia.gemelo_id == gemelo.id,
            GemeloCompetencia.nivel_demostrado.is_(None),
            GemeloCompetencia.competencia_uri.not_in(validas),
            sin_respaldo,
        )
    )
    for c in unicas.values():
        if c.uri not in validas:
            continue
        competencia = s.get(GemeloCompetencia, (gemelo.id, c.uri))
        if competencia is None:
            competencia = GemeloCompetencia(gemelo_id=gemelo.id, competencia_uri=c.uri)
            s.add(competencia)
        competencia.nivel_declarado = NIVEL_DECLARADO
        s.add(
            Evidencia(
                gemelo_id=gemelo.id,
                competencia_uri=c.uri,
                origen="cv",
                fragmento=c.termino[:500],  # sin revertir: nunca vuelven datos personales
                puntuacion=c.similitud,
            )
        )
    gemelo.trayectoria = perfil.model_dump(exclude={"nivel_ingles"})
    gemelo.nivel_ingles = perfil.nivel_ingles
    s.commit()


def trayectoria_cambia(gemelo: Gemelo | None, perfil: PerfilCv) -> bool:
    if gemelo is None:
        return True
    guardado = (gemelo.trayectoria, gemelo.nivel_ingles)
    return guardado != (perfil.model_dump(exclude={"nivel_ingles"}), perfil.nivel_ingles)
