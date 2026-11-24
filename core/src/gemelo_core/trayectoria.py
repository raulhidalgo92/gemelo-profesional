# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Trayectoria del CV: resumen, experiencias, formación y nivel de inglés.

Minimización (RGPD): de cada puesto solo se guardan el cargo, el sector y los años, sin
el nombre de la empresa; de cada titulación, sin el centro. El texto llega seudonimizado
y, por si el modelo copiara algún marcador de dato ocultado, se elimina de la respuesta.
"""

import re
from datetime import date
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from gemelo_core.extraccion import MAX_CARACTERES_CV, _pedir_json
from gemelo_core.ia import ClienteIA

PROMPT_TRAYECTORIA = (Path(__file__).parent / "prompts" / "trayectoria_cv.md").read_text("utf-8")
MAX_ELEMENTOS = 15
NIVELES_INGLES = ("A1", "A2", "B1", "B2", "C1", "C2")
_MARCADOR = re.compile(r"\[[A-Z_]+_\d+\]")


def _limpiar(valor: object) -> object:
    """Quita marcadores de datos ocultados y espacios sobrantes."""
    if not isinstance(valor, str):
        return valor
    return " ".join(_MARCADOR.sub("", valor).split()) or None


def _anio(valor: object) -> int | None:
    """Un año razonable o nada: el modelo a veces devuelve «actualidad» o fechas raras."""
    try:
        anio = int(valor)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        return None
    return anio if 1950 <= anio <= 2100 else None


def _nivel(valor: object) -> str | None:
    nivel = valor.strip().upper() if isinstance(valor, str) else None
    return nivel if nivel in NIVELES_INGLES else None


Texto = Annotated[str, BeforeValidator(_limpiar)]
Anio = Annotated[int | None, BeforeValidator(_anio)]


class Experiencia(BaseModel):
    puesto: Annotated[Texto, Field(max_length=120)]
    sector: Annotated[Texto | None, Field(max_length=60)] = None
    inicio: Anio = None
    fin: Anio = None  # sin fin: trabajo actual


class Formacion(BaseModel):
    titulo: Annotated[Texto, Field(max_length=160)]
    inicio: Anio = None
    fin: Anio = None


class Trayectoria(BaseModel):
    resumen: Annotated[Texto | None, Field(max_length=600)] = None
    experiencias: list[Experiencia] = []
    formacion: list[Formacion] = []

    @model_validator(mode="before")
    @classmethod
    def _sin_vacios(cls, datos: object) -> object:
        """Descarta puestos sin cargo y estudios sin título, y recorta listas largas."""
        if isinstance(datos, dict):
            datos = dict(datos)
            for lista, clave in (("experiencias", "puesto"), ("formacion", "titulo")):
                validos = [e for e in datos.get(lista) or [] if isinstance(e, dict)]
                datos[lista] = [e for e in validos if _limpiar(e.get(clave))][:MAX_ELEMENTOS]
        return datos


class PerfilCv(Trayectoria):
    """Lo que se extrae del CV además de las competencias."""

    nivel_ingles: Annotated[str | None, BeforeValidator(_nivel)] = None


def extraer_perfil(ia: ClienteIA, texto: str, modelo: str | None = None) -> PerfilCv:
    """Trayectoria y nivel de inglés de un CV ya seudonimizado."""
    # Sin el año actual, el modelo calcula mal los años de experiencia
    entrada = f"Año actual: {date.today().year}\n\nCurrículum:\n{texto[:MAX_CARACTERES_CV]}"
    mensajes = [
        {"role": "system", "content": PROMPT_TRAYECTORIA},
        {"role": "user", "content": entrada},
    ]
    return _pedir_json(ia, mensajes, PerfilCv, modelo)
