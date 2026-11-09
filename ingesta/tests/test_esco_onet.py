# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from ingesta.fuentes import esco_onet

ESCO = "http://data.europa.eu/esco"
CABECERA = (
    "O*NET Id,O*NET Title,O*NET Description,"
    "ESCO or ISCO URI,ESCO or ISCO Title,ESCO or ISCO Description,Type of Match"
)
CSV = "\n".join(
    [
        "﻿Mapping project name,ESCO-O*NET Crosswalk,,,,,",
        "Classification 1 Name,O*NET,,,,,",
        ",,,,,,",
        CABECERA,
        f'15-1252.00,Software Developers,"Design, develop.",{ESCO}/occupation/abc,dev,D,exactMatch',
        f"15-1252.00,Software Developers,D,{ESCO}/occupation/def,web dev,D,narrowMatch",
        f"11-1011.00,Chief Executives,D,{ESCO}/isco/C1120,managing directors,D,exactISCO",
    ]
)


def test_salta_metadatos_y_descarta_grupos_isco():
    assert list(esco_onet.filas(CSV)) == [
        {
            "ocupacion_uri": f"{ESCO}/occupation/abc",
            "onet_codigo": "15-1252.00",
            "tipo_correspondencia": "exactMatch",
        },
        {
            "ocupacion_uri": f"{ESCO}/occupation/def",
            "onet_codigo": "15-1252.00",
            "tipo_correspondencia": "narrowMatch",
        },
    ]
