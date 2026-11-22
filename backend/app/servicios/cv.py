# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Análisis del currículum: texto → seudonimización → competencias ESCO declaradas.

RGPD: el archivo se procesa en memoria y nunca se guarda. Antes de enviar el texto al
modelo de lenguaje se sustituyen los datos identificativos por marcadores, y del CV solo
se conservan las competencias y el término del que se dedujo cada una.
"""

import io
import zipfile
from dataclasses import dataclass

from docx import Document
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from gemelo_core.extraccion import asociar_a_esco, proponer_terminos
from gemelo_core.ia import ClienteIA
from gemelo_core.modelos import Evidencia, Gemelo, GemeloCompetencia, Usuario
from gemelo_core.seudonimizacion import seudonimizar

MAX_BYTES = 5 * 1024 * 1024
MIN_CARACTERES = 200
NIVEL_DECLARADO = 0.5  # declarada en el CV, sin evidencia todavía


class ErrorCv(Exception):
    def __init__(self, codigo: str):
        super().__init__(codigo)
        self.codigo = codigo


@dataclass
class CompetenciaCv:
    uri: str
    titulo: str
    termino: str


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


def analizar(s: Session, ia: ClienteIA, usuario: Usuario, texto: str) -> list[CompetenciaCv]:
    """Sustituye las competencias declaradas del gemelo por las del CV."""
    seudo = seudonimizar(texto, nombres=nombres_a_ocultar(texto, usuario.nombre))
    terminos = proponer_terminos(ia, seudo.texto, cv=True)
    detectadas = asociar_a_esco(s, ia, terminos, contexto="currículum de un profesional")

    gemelo = s.scalar(select(Gemelo).where(Gemelo.usuario_id == usuario.id))
    if gemelo is None:
        gemelo = Gemelo(usuario_id=usuario.id)
        s.add(gemelo)
        s.flush()
    # Un CV nuevo sustituye al anterior; lo demostrado en entrevistas se conserva
    s.execute(delete(Evidencia).where(Evidencia.gemelo_id == gemelo.id, Evidencia.origen == "cv"))
    s.execute(
        delete(GemeloCompetencia).where(
            GemeloCompetencia.gemelo_id == gemelo.id, GemeloCompetencia.nivel_demostrado.is_(None)
        )
    )
    existentes = set(
        s.scalars(
            select(GemeloCompetencia.competencia_uri).where(
                GemeloCompetencia.gemelo_id == gemelo.id
            )
        )
    )
    for c in detectadas:
        if c.uri in existentes:
            s.get(GemeloCompetencia, (gemelo.id, c.uri)).nivel_declarado = NIVEL_DECLARADO
        else:
            s.add(
                GemeloCompetencia(
                    gemelo_id=gemelo.id, competencia_uri=c.uri, nivel_declarado=NIVEL_DECLARADO
                )
            )
        s.add(
            Evidencia(
                gemelo_id=gemelo.id,
                competencia_uri=c.uri,
                origen="cv",
                fragmento=c.termino[:500],  # sin revertir: nunca vuelven datos personales
                puntuacion=c.similitud,
            )
        )
    s.commit()
    return [CompetenciaCv(c.uri, c.titulo, c.termino) for c in detectadas]
