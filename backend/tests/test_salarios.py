# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.deps import obtener_sesion
from app.api.mercado import gran_grupo, subgrupos_por_frecuencia
from app.main import app


def teardown_function():
    app.dependency_overrides.clear()


def test_gran_grupo_de_cada_subgrupo():
    assert gran_grupo("27") == "C"
    assert gran_grupo("38") == "D"
    assert gran_grupo("44") == "F"
    assert gran_grupo("00") == "Q"


def test_subgrupos_ordenados_por_frecuencia_con_desempate_estable():
    assert subgrupos_por_frecuencia(["3820", "2711", "2712"]) == ["27", "38"]
    assert subgrupos_por_frecuencia(["5110", "5020"]) == ["50", "51"]
    assert subgrupos_por_frecuencia([]) == []


def test_ocupacion_inexistente_devuelve_404():
    sesion = MagicMock()
    sesion.get.return_value = None
    app.dependency_overrides[obtener_sesion] = lambda: sesion
    r = TestClient(app).get("/api/mercado/salarios", params={"ocupacion": "x"})
    assert r.status_code == 404
