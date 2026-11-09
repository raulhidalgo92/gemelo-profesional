# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.deps import obtener_cliente_ia, obtener_sesion
from app.main import app
from gemelo_core.ia import ErrorIA

FILA = SimpleNamespace(uri="u1", titulo="TypeScript", tipo="knowledge", sim=0.4, dist=0.39)


def _cliente(ia) -> tuple[TestClient, MagicMock]:
    sesion = MagicMock()
    sesion.execute.return_value = [FILA]
    app.dependency_overrides[obtener_sesion] = lambda: sesion
    app.dependency_overrides[obtener_cliente_ia] = lambda: ia
    return TestClient(app), sesion


def teardown_function():
    app.dependency_overrides.clear()


def test_busqueda_semantica_por_defecto():
    ia = MagicMock()
    ia.embeddings.return_value = [[0.1] * 1024]
    cliente, _ = _cliente(ia)
    r = cliente.get("/api/competencias", params={"q": "Angular"})
    assert r.status_code == 200
    assert r.json()["modo"] == "semantico"
    assert r.json()["resultados"][0] == {
        "uri": "u1",
        "titulo": "TypeScript",
        "tipo": "knowledge",
        "similitud": 0.61,
    }
    ia.embeddings.assert_called_once()


def test_si_la_ia_falla_busca_por_texto():
    ia = MagicMock()
    ia.embeddings.side_effect = ErrorIA("sin conexión")
    r = _cliente(ia)[0].get("/api/competencias", params={"q": "Angular"})
    assert r.json()["modo"] == "texto"
    assert r.json()["resultados"][0]["similitud"] == 0.4


def test_sin_ia_configurada_busca_por_texto():
    r = _cliente(None)[0].get("/api/competencias", params={"q": "Angular"})
    assert r.json()["modo"] == "texto"


def test_modo_texto_explicito_no_usa_la_ia():
    ia = MagicMock()
    r = _cliente(ia)[0].get("/api/competencias", params={"q": "Angular", "modo": "texto"})
    assert r.json()["modo"] == "texto"
    ia.embeddings.assert_not_called()
