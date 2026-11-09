# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Salarios por ocupación del Instituto Nacional de Estadística (INE).

Se usan dos operaciones estadísticas, ambas con ganancia bruta anual por trabajador:

- Encuesta Cuatrienal de Estructura Salarial (2022): media y percentiles (P10, P25,
  mediana, P75, P90) por subgrupo principal de la CNO-11 (2 dígitos). Es la más detallada.
- Encuesta Anual de Estructura Salarial: media por gran grupo de la CNO-11 (letras A-Q)
  de los últimos años. Menos detalle, pero más reciente y permite ver la tendencia.

Para enlazarlo con ESCO (que usa ISCO-08) se carga también la correspondencia oficial
CNO-11 ↔ CIUO-08 publicada por el INE.

Se cargan solo los datos de ambos sexos y total nacional. La API del INE (Tempus) es
pública y no necesita registro. Un valor negativo indica que la cifra se basa en pocas
observaciones (100-500): se guarda en positivo con la marca ``precision_baja``.
"""

import logging
from collections.abc import Iterable, Iterator
from pathlib import Path

import httpx
import xlrd

from gemelo_core.db import sesion
from gemelo_core.modelos import CorrespondenciaCnoIsco, EstadisticaSalarial
from ingesta.fuentes._util import lotes, upsert

log = logging.getLogger(__name__)

API = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA"
URL_CORRESPONDENCIA = "https://www.ine.es/daco/daco42/clasificaciones/corr_cno11_ciuo08.xls"
FICHERO_CORRESPONDENCIA = "corr_cno11_ciuo08.xls"

# (fuente, tabla Tempus, nº de periodos a pedir)
TABLAS = [
    ("INE-EES", 36830, 1),  # cuatrienal: subgrupos CNO-11 con percentiles
    ("INE-EAES", 28186, 10),  # anual: grandes grupos CNO-11
]

MEDIDAS = {
    "Media": "media",
    "Salario medio bruto": "media",
    "Mediana": "mediana",
    "Percentil 10": "p10",
    "Cuartil inferior": "p25",
    "Cuartil superior": "p75",
    "Percentil 90": "p90",
}
TOTAL = "TOTAL"


def _codigo(valor: object) -> str:
    """Normaliza un código de la hoja de cálculo (puede venir como número)."""
    if isinstance(valor, float):
        valor = int(valor)
    return str(valor).strip().zfill(4) if str(valor).strip() else ""


def filas_correspondencia(libro: xlrd.book.Book) -> Iterator[dict]:
    """Pares CNO-11 ↔ ISCO-08 de 4 dígitos. Se salta la cabecera y los códigos ISCO
    sin equivalente en España (filas sin CNO)."""
    hoja = libro.sheet_by_index(0)
    vistos: set[tuple[str, str]] = set()
    for i in range(hoja.nrows):
        fila = hoja.row_values(i)
        if len(fila) < 4:
            continue
        cno, isco = _codigo(fila[0]), _codigo(fila[3])
        if not (cno.isdigit() and isco.isdigit()) or (cno, isco) in vistos:
            continue
        vistos.add((cno, isco))
        yield {"cno": cno, "isco": isco, "titulo_cno": str(fila[1]).strip()[:255]}


def filas_salarios(series: Iterable[dict], fuente: str) -> Iterator[dict]:
    """Convierte las series de la API Tempus en filas de ``estadistica_salarial``."""
    for serie in series:
        meta = {m["T3_Variable"]: m for m in serie.get("MetaData", [])}
        if meta.get("Sexo", {}).get("Nombre") != "Ambos sexos":
            continue
        if "OCUPACIONES" in meta:
            codigo = meta["OCUPACIONES"]["Codigo"]
            descripcion = meta["OCUPACIONES"]["Nombre"]
        elif "TOTALES OCUPACIONES" in meta:
            codigo, descripcion = TOTAL, "Todas las ocupaciones"
        else:
            continue
        medida = next((MEDIDAS[m["Nombre"]] for m in meta.values() if m["Nombre"] in MEDIDAS), None)
        if not codigo or medida is None:
            continue
        for dato in serie.get("Data", []):
            if dato.get("Valor") is None:  # el INE no publica cifras con < 100 observaciones
                continue
            yield {
                "fuente": fuente,
                "codigo_ocupacion": codigo,
                "descripcion": descripcion[:255],
                "periodo": str(dato["Anyo"]),
                "medida": medida,
                "valor": abs(dato["Valor"]),
                "precision_baja": dato["Valor"] < 0,
            }


def _descargar_correspondencia(cliente: httpx.Client, destino: Path) -> Path:
    ruta = destino / FICHERO_CORRESPONDENCIA
    if not ruta.exists():
        destino.mkdir(parents=True, exist_ok=True)
        log.info("Descargando correspondencia CNO-11 ↔ CIUO-08 del INE")
        r = cliente.get(URL_CORRESPONDENCIA)
        r.raise_for_status()
        ruta.write_bytes(r.content)
    return ruta


def cargar(directorio: Path) -> None:
    with httpx.Client(timeout=120, follow_redirects=True) as cliente:
        libro = xlrd.open_workbook(str(_descargar_correspondencia(cliente, directorio)))
        correspondencias = list(filas_correspondencia(libro))

        salarios: list[dict] = []
        for fuente, tabla, periodos in TABLAS:
            log.info("Descargando tabla %s del INE (%s)", tabla, fuente)
            r = cliente.get(f"{API}/{tabla}", params={"nult": periodos, "tip": "AM"})
            r.raise_for_status()
            salarios.extend(filas_salarios(r.json(), fuente))

    with sesion() as s:
        for lote in lotes(correspondencias):
            upsert(s, CorrespondenciaCnoIsco, lote, ["cno", "isco"])
        claves = ["fuente", "codigo_ocupacion", "periodo", "medida"]
        for lote in lotes(salarios):
            upsert(s, EstadisticaSalarial, lote, claves)
        s.commit()
    log.info(
        "INE: %d correspondencias CNO-ISCO y %d datos salariales",
        len(correspondencias),
        len(salarios),
    )
