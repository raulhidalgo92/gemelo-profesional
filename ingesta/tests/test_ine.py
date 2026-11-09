# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace

from ingesta.fuentes import ine


def _libro(filas: list[list]):
    hoja = SimpleNamespace(nrows=len(filas), row_values=lambda i: filas[i])
    return SimpleNamespace(sheet_by_index=lambda _: hoja)


def _serie(ocupacion: tuple[str, str] | None, sexo: str, medida: str, datos: list) -> dict:
    meta = [
        {"T3_Variable": "Sexo", "Nombre": sexo, "Codigo": ""},
        {"T3_Variable": "Percentiles simples", "Nombre": medida, "Codigo": ""},
    ]
    if ocupacion:
        meta.append({"T3_Variable": "OCUPACIONES", "Codigo": ocupacion[0], "Nombre": ocupacion[1]})
    else:
        meta.append({"T3_Variable": "TOTALES OCUPACIONES", "Nombre": "Todas", "Codigo": ""})
    return {"MetaData": meta, "Data": [{"Anyo": a, "Valor": v} for a, v in datos]}


def test_correspondencia_salta_cabecera_y_codigos_sin_equivalente():
    libro = _libro(
        [
            ["Correspondencia CN0-11 con CIUO08"],
            ["CNO11", "TITULO11", "FREC11", "CIUO08", "TITULO08", "FREC08", "COMENTARIO"],
            ["", "", "", "3253", "Trabajadores comunitarios", "1", "No aplicable a España"],
            ["2712", "Analistas y diseñadores de software", "1", "2512", "Dev", "1", ""],
            [11.0, "Oficiales de las fuerzas armadas", "1", 110.0, "Oficiales", "1", ""],
            ["2712", "Analistas y diseñadores de software", "1", "2512", "Dev", "1", ""],
        ]
    )
    assert list(ine.filas_correspondencia(libro)) == [
        {"cno": "2712", "isco": "2512", "titulo_cno": "Analistas y diseñadores de software"},
        {"cno": "0011", "isco": "0110", "titulo_cno": "Oficiales de las fuerzas armadas"},
    ]


def test_salarios_solo_ambos_sexos_y_marca_precision_baja():
    series = [
        _serie(("27", "Profesionales TIC"), "Ambos sexos", "Mediana", [(2022, 38000.5)]),
        _serie(("27", "Profesionales TIC"), "Mujeres", "Mediana", [(2022, 35000.0)]),
        _serie(("61", "Agrícolas"), "Ambos sexos", "Percentil 90", [(2022, -30000.0)]),
        _serie(("62", "Ganaderos"), "Ambos sexos", "Media", [(2022, None)]),
        _serie(None, "Ambos sexos", "Cuartil inferior", [(2022, 17000.0)]),
    ]
    filas = list(ine.filas_salarios(series, "INE-EES"))
    assert [
        (f["codigo_ocupacion"], f["medida"], f["valor"], f["precision_baja"]) for f in filas
    ] == [
        ("27", "mediana", 38000.5, False),
        ("61", "p90", 30000.0, True),
        (ine.TOTAL, "p25", 17000.0, False),
    ]
    assert filas[0]["periodo"] == "2022" and filas[0]["fuente"] == "INE-EES"
