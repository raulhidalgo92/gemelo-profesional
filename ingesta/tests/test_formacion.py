# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from datetime import date

from ingesta.fuentes import cursos_soc, sepe_formacion


def test_separa_las_ocupaciones_relacionadas():
    celda = (
        "29341012 - AYUDANTES DE DIRECCIÓN DE CINE, 29341094 - DIRECTORES-REALIZADORES DE CINE, "
        "37231011 - MONITORES DE ACTIVIDADES RECREATIVAS, DE OCIO Y TIEMPO LIBRE"
    )
    assert sepe_formacion.ocupaciones(celda) == [
        ("29341012", "AYUDANTES DE DIRECCIÓN DE CINE"),
        ("29341094", "DIRECTORES-REALIZADORES DE CINE"),
        ("37231011", "MONITORES DE ACTIVIDADES RECREATIVAS, DE OCIO Y TIEMPO LIBRE"),
    ]
    assert sepe_formacion.ocupaciones("-") == []


def test_ocupaciones_con_codigos_de_4_y_6_digitos():
    celda = "111010 - OFICIALES DE LAS FUERZAS ARMADAS, 2712 - ANALISTAS DE SOFTWARE, 14211010 - "
    assert sepe_formacion.ocupaciones(celda) == [
        ("00111010", "OFICIALES DE LAS FUERZAS ARMADAS"),
        ("2712", "ANALISTAS DE SOFTWARE"),
        ("14211010", ""),
    ]


def test_normaliza_una_especialidad():
    fila = {
        "CÓDIGO": "ENAE30",
        "DENOMINACIÓN": "TECNICO DE SISTEMAS DE ENERGIAS RENOVABLES",
        "VERSIÓN": "1",
        "FAMILIA PROFESIONAL": "ENERGÍA Y AGUA",
        "ÁREA PROFESIONAL": "ENERGÍAS RENOVABLES",
        "COMPETENCIA TRANSVERSAL": "-",
        "NIVEL DE CUALIFICACIÓN": "Sin especificar",
        "MODALIDAD DE IMPARTICIÓN": "Solo Presencial",
        "DURACIÓN TOTAL": "600",
        "DURACIÓN TOTAL DE LA PARTE PRESENCIAL (TELEFORMACIÓN O MIXTA)": "-",
    }
    e = sepe_formacion.normalizar_especialidad(fila)
    assert e["codigo"] == "ENAE30" and e["horas"] == 600
    assert e["nivel"] is None and e["horas_presenciales"] is None
    assert e["competencia_transversal"] is None


def test_curso_soc_con_fechas_en_formato_americano():
    curso = {
        "curs": "480200",
        "tipus": "Formació ocupacional",
        "especialitat_formativa": "ACTIVITATS AUXILIARS EN VIVERS.",
        "municipi_especialitat": "CASTELLAR DEL VALLÈS",
        "provincia_especialitat": "BARCELONA",
        "modalitat": "PRESENCIAL",
        "data_inici": "11/17/2026",
        "data_fi": "05/28/2027",
        "hores": "330",
        "nom_centre": "INSTITUT LES GARBERES",
        "telefon_centre": "937000000",
    }
    [c] = cursos_soc.filas([curso, {"curs": "", "especialitat_formativa": "X"}])
    assert c["fecha_inicio"] == date(2026, 11, 17) and c["fecha_fin"] == date(2027, 5, 28)
    assert c["denominacion"] == "ACTIVITATS AUXILIARS EN VIVERS"
    assert c["provincia"] == "Barcelona" and c["horas"] == 330
    assert "telefon_centre" not in c and "937000000" not in c.values()
