# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.deps import obtener_sesion
from app.main import app


def _cliente_con_sesion(sesion: MagicMock) -> TestClient:
    app.dependency_overrides[obtener_sesion] = lambda: sesion
    return TestClient(app)


def test_salud_ok():
    cliente = _cliente_con_sesion(MagicMock())
    r = cliente.get("/api/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"
    assert r.json()["base_datos"] is True


def test_salud_sin_base_datos():
    sesion = MagicMock()
    sesion.execute.side_effect = OperationalError("SELECT 1", {}, Exception("sin conexión"))
    r = _cliente_con_sesion(sesion).get("/api/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "degradado"


def teardown_function():
    app.dependency_overrides.clear()
