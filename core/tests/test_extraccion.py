# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace

import pytest

from gemelo_core.extraccion import Candidata, elegir, proponer_terminos, texto_eleccion
from gemelo_core.ia import ErrorIA


class IAFalsa:
    """Devuelve las respuestas indicadas, en orden, y guarda los mensajes recibidos."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.mensajes = []
        self.cfg = SimpleNamespace(llm_modelo_ligero="ligero")

    def completar_json(self, mensajes, **_):
        self.mensajes.append(mensajes)
        return self.respuestas.pop(0)


EXCEL = [Candidata("u1", "utilizar software de hojas de cálculo", 0.63)]
PUNTUALIDAD = [
    Candidata("u2", "garantizar el horario de los trenes", 0.71),
    Candidata("u3", "cumplir los horarios", 0.69),
]


def test_propone_terminos_sin_repetidos_ni_vacios():
    ia = IAFalsa({"competencias": ["Excel", " Excel ", "", "inglés"]})
    assert proponer_terminos(ia, "Administrativo con Excel e inglés") == ["Excel", "inglés"]


def test_reintenta_una_vez_si_el_formato_es_incorrecto():
    ia = IAFalsa({"otra_cosa": []}, {"competencias": ["SQL"]})
    assert proponer_terminos(ia, "Analista con SQL") == ["SQL"]
    assert "Formato incorrecto" in ia.mensajes[1][-1]["content"]


def test_error_controlado_si_el_formato_sigue_mal():
    ia = IAFalsa({"x": 1}, {"y": 2})
    with pytest.raises(ErrorIA):
        proponer_terminos(ia, "texto")


def test_el_texto_de_eleccion_numera_terminos_y_candidatas():
    texto = texto_eleccion("Limpieza", ["Excel", "puntualidad"], [EXCEL, PUNTUALIDAD])
    assert "1. «Excel»\n   1) utilizar software de hojas de cálculo" in texto
    assert "2. «puntualidad»\n   1) garantizar el horario de los trenes\n   2) cumplir" in texto


def test_elige_candidatas_y_descarta_indices_invalidos():
    respuesta = {
        "elecciones": [
            {"termino": 1, "candidata": 1},
            {"termino": "puntualidad", "candidata": 2},  # a veces devuelve el texto
            {"termino": 2, "candidata": 9},  # índice inventado
            {"termino": 7, "candidata": 1},
        ]
    }
    detectadas = elegir(
        IAFalsa(respuesta), "Limpieza", ["Excel", "puntualidad"], [EXCEL, PUNTUALIDAD]
    )
    assert [(c.uri, c.termino) for c in detectadas] == [("u3", "puntualidad"), ("u1", "Excel")]


def test_null_significa_que_ninguna_candidata_encaja():
    respuesta = {"elecciones": [{"termino": 1, "candidata": None}]}
    assert elegir(IAFalsa(respuesta), "Limpieza", ["puntualidad"], [PUNTUALIDAD]) == []
