# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.deps import obtener_sesion
from app.api.formacion import agrupar
from app.main import app
from gemelo_core.modelos import EspecialidadFormativa


def teardown_function():
    app.dependency_overrides.clear()


def _especialidad(codigo: str, nivel: int | None) -> EspecialidadFormativa:
    return EspecialidadFormativa(
        codigo=codigo, denominacion=f"Curso {codigo}", nivel=nivel, horas=100
    )


def test_agrupa_por_especialidad_y_explica_el_motivo():
    a, b, c = _especialidad("A", 2), _especialidad("B", 3), _especialidad("C", 1)
    filas = [
        (a, "PROGRAMADORES WEB"),
        (b, "PROGRAMADORES WEB"),
        (c, "PROGRAMADORES WEB"),
        (c, "ANALISTAS DE SISTEMAS"),
    ]
    resultado = agrupar(filas, limite=2)
    # C comparte dos ocupaciones; entre A y B gana el nivel más alto
    assert [e.codigo for e in resultado] == ["C", "B"]
    assert resultado[0].motivo == "Prepara para: Analistas de sistemas; Programadores web"


def test_ocupacion_inexistente_devuelve_404():
    sesion = MagicMock()
    sesion.get.return_value = None
    app.dependency_overrides[obtener_sesion] = lambda: sesion
    r = TestClient(app).get("/api/formacion/especialidades", params={"ocupacion": "x"})
    assert r.status_code == 404
