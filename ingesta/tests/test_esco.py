# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from ingesta.fuentes import esco, infojobs

OCUPACIONES = (
    "conceptType,conceptUri,iscoGroup,preferredLabel,altLabels,description,code\n"
    "Occupation,http://data.europa.eu/esco/occupation/1,2512,desarrollador de software,"
    '"programador\nprogramadora",Desarrolla software.,2512.4\n'
)


def test_parsea_ocupaciones(tmp_path: Path):
    ruta = tmp_path / "occupations_es.csv"
    ruta.write_text(OCUPACIONES, encoding="utf-8")
    filas = list(esco.filas_ocupaciones(ruta))
    assert len(filas) == 1
    assert filas[0]["titulo"] == "desarrollador de software"
    assert filas[0]["grupo_isco"] == "2512"
    assert "programadora" in filas[0]["titulos_alternativos"]


def test_normaliza_oferta_infojobs():
    oferta = {
        "id": "abc123",
        "title": " Desarrollador Angular ",
        "province": {"id": 26, "value": "La Rioja"},
        "city": "Logroño",
        "link": "https://www.infojobs.net/x",
        "author": {"name": "Empresa SL"},
        "published": "2026-11-01T10:00:00.000Z",
    }
    fila = infojobs.normalizar(oferta)
    assert fila["fuente"] == "infojobs"
    assert fila["titulo"] == "Desarrollador Angular"
    assert fila["provincia"] == "La Rioja"
    assert str(fila["publicada_en"]) == "2026-11-01"
