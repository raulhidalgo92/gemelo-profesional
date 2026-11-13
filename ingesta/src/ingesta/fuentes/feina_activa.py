# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Ofertas del portal Feina Activa del Servei Públic d'Ocupació de Catalunya (SOC).

Datos abiertos de la Generalitat de Catalunya (catálogo datos.gob.es), un único XML
con todas las ofertas vigentes que se actualiza a diario. No incluye datos de contacto
personales; aun así el texto se limpia antes de guardarlo.
Cita obligatoria: «Generalitat de Catalunya. Departament d'Empresa i Treball».
"""

import xml.etree.ElementTree as ET
from collections.abc import Iterator
from datetime import date, datetime

import httpx

from ingesta.fuentes._ofertas import guardar

FUENTE = "feina_activa"
URL = "https://feinaactiva.gencat.cat/api/offers/offers-xml"

# Las cifras sin periodo indicado son mensuales salvo que sean claramente anuales.
SALARIO_ANUAL_MINIMO = 6000

SECCIONES = [
    ("experience", "Experiencia"),
    ("requirements", "Requisitos"),
    ("studies", "Estudios"),
    ("contract", "Contrato"),
    ("workingHours", "Jornada"),
]


def _texto(ad: ET.Element, campo: str) -> str:
    return (ad.findtext(campo) or "").strip()


def _fecha(valor: str) -> date | None:
    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()
    except ValueError:
        return None


def _numero(valor: str) -> float | None:
    try:
        return float(valor) if valor else None
    except ValueError:
        return None


def normalizar(ad: ET.Element) -> dict:
    """Convierte una oferta del XML al esquema común `oferta`."""
    partes = [_texto(ad, "content")]
    partes += [f"{nombre}: {_texto(ad, campo)}" for campo, nombre in SECCIONES if _texto(ad, campo)]
    salario_min, salario_max = _numero(_texto(ad, "salaryMin")), _numero(_texto(ad, "salaryMax"))
    referencia = salario_max or salario_min
    return {
        "fuente": FUENTE,
        "id_externo": _texto(ad, "id"),
        "titulo": _texto(ad, "title")[:512],
        "empresa": _texto(ad, "company")[:255] or None,
        "provincia": _texto(ad, "region").title() or None,
        "ubicacion": _texto(ad, "city").title() or None,
        "salario_min": salario_min,
        "salario_max": salario_max,
        "salario_periodo": (
            None if referencia is None else "año" if referencia >= SALARIO_ANUAL_MINIMO else "mes"
        ),
        "texto": "\n\n".join(p for p in partes if p),
        "url": _texto(ad, "url")[:1024] or None,
        "publicada_en": _fecha(_texto(ad, "date")),
    }


def filas(contenido: bytes) -> Iterator[dict]:
    for ad in ET.fromstring(contenido).iter("ad"):
        if _texto(ad, "id") and _texto(ad, "title"):
            yield normalizar(ad)


def ingerir() -> int:
    r = httpx.get(URL, timeout=120)
    r.raise_for_status()
    return guardar(FUENTE, list(filas(r.content)))
