# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
import io
import zipfile
from pathlib import Path

import pytest

from ingesta.fuentes import onet

OCUPACIONES = "O*NET-SOC Code\tTitle\tDescription\n15-1252.00\tSoftware Developers\tDesarrollan.\n"
RELACIONADAS = (
    "O*NET-SOC Code\tRelated O*NET-SOC Code\tRelatedness Tier\tIndex\n"
    "15-1252.00\t15-1253.00\tPrimary-Short\t1\n"
)


def _zip(ficheros: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for nombre, contenido in ficheros.items():
            z.writestr(nombre, contenido)
    return buffer.getvalue()


def test_extrae_solo_los_ficheros_necesarios(tmp_path: Path):
    contenido = _zip(
        {
            "db_31_0_text/Occupation Data.txt": OCUPACIONES,
            "db_31_0_text/Related Occupations.txt": RELACIONADAS,
            "db_31_0_text/Skills.txt": "no se usa",
        }
    )
    onet.extraer(contenido, tmp_path / "onet")
    assert sorted(p.name for p in (tmp_path / "onet").iterdir()) == list(onet.FICHEROS)

    transiciones = list(onet.filas_transiciones(tmp_path / "onet" / "Related Occupations.txt"))
    assert transiciones == [
        {"origen": "15-1252.00", "destino": "15-1253.00", "nivel": "Primary-Short", "indice": 1}
    ]


def test_zip_incompleto_da_error(tmp_path: Path):
    with pytest.raises(ValueError, match="Related Occupations"):
        onet.extraer(_zip({"Occupation Data.txt": OCUPACIONES}), tmp_path)
