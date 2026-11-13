# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Seudonimización de texto antes de enviarlo a un modelo de lenguaje externo (RGPD).

Sustituye datos identificativos evidentes por marcadores reversibles. Es una
primera versión basada en expresiones regulares; se ampliará con detección de
nombres propios y se medirá su cobertura en la evaluación.
"""

import re
from dataclasses import dataclass, field

PATRONES: dict[str, re.Pattern[str]] = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "TELEFONO": re.compile(r"(?<!\d)(?:\+34[\s-]?)?[6789]\d{2}[\s-]?\d{3}[\s-]?\d{3}(?!\d)"),
    "DNI": re.compile(r"\b\d{8}[A-HJ-NP-TV-Z]\b", re.IGNORECASE),
    "NIE": re.compile(r"\b[XYZ]\d{7}[A-HJ-NP-TV-Z]\b", re.IGNORECASE),
    "URL_PERFIL": re.compile(r"https?://(?:www\.)?linkedin\.com/in/[\w-]+/?", re.IGNORECASE),
}


@dataclass
class Seudonimizado:
    texto: str
    tabla: dict[str, str] = field(default_factory=dict)

    def revertir(self, texto: str) -> str:
        for marcador, original in self.tabla.items():
            texto = texto.replace(marcador, original)
        return texto


def seudonimizar(texto: str, nombres: list[str] | None = None) -> Seudonimizado:
    """Reemplaza datos personales por marcadores [TIPO_n]."""
    tabla: dict[str, str] = {}
    contadores: dict[str, int] = {}

    def sustituir(tipo: str, valor: str) -> str:
        for marcador, original in tabla.items():
            if original == valor:
                return marcador
        contadores[tipo] = contadores.get(tipo, 0) + 1
        marcador = f"[{tipo}_{contadores[tipo]}]"
        tabla[marcador] = valor
        return marcador

    # Primero URL (contienen texto que podría confundirse con otros patrones)
    for tipo in ("URL_PERFIL", "EMAIL", "DNI", "NIE", "TELEFONO"):
        texto = PATRONES[tipo].sub(lambda m, t=tipo: sustituir(t, m.group(0)), texto)

    for nombre in nombres or []:
        if nombre.strip():
            patron = re.compile(re.escape(nombre.strip()), re.IGNORECASE)
            texto = patron.sub(lambda m: sustituir("NOMBRE", m.group(0)), texto)

    return Seudonimizado(texto=texto, tabla=tabla)


# Nombre propio tras expresiones como «preguntar por» o «persona de contacto:».
_NOMBRE_CONTACTO = re.compile(
    r"(?P<antes>(?i:(?:preguntar|pregunte|contactar|contacte|dirigirse)\s+(?:por|con|a)"
    r"|persona\s+de\s+contacto\s*:?))\s+"
    r"(?:(?:D\.|Dña\.|Sr\.|Sra\.)\s*)?"
    r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2}",
)


def eliminar_datos_contacto(texto: str) -> str:
    """Borra de forma irreversible emails, teléfonos, documentos y nombres de contacto.

    Se usa con datos de terceros (por ejemplo, ofertas de empleo) que no necesitamos
    conservar: a diferencia de `seudonimizar`, no guarda la correspondencia.
    """
    for tipo in ("URL_PERFIL", "EMAIL", "DNI", "NIE", "TELEFONO"):
        texto = PATRONES[tipo].sub("[contacto]", texto)
    return _NOMBRE_CONTACTO.sub(lambda m: f"{m.group('antes')} [contacto]", texto)
