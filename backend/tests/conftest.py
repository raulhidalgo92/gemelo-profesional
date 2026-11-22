# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Base de datos de pruebas para los tests que la necesitan (cuentas de usuario).

Se usa la base indicada en TEST_DATABASE_URL; si no está definida, esos tests se omiten.
En Docker: TEST_DATABASE_URL=postgresql+psycopg://gemelo:<clave>@db:5432/gemelo_test
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.api.deps import obtener_sesion
from app.main import app
from gemelo_core.modelos import Base

URL = os.environ.get("TEST_DATABASE_URL")


def _crear_base_si_falta(url: str) -> None:
    destino = make_url(url)
    admin = create_engine(destino.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        if not c.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": destino.database}
        ):
            c.execute(text(f'CREATE DATABASE "{destino.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def motor_pruebas():
    if not URL:
        pytest.skip("TEST_DATABASE_URL no definida")
    _crear_base_si_falta(URL)
    motor = create_engine(URL)
    with motor.begin() as c:
        for ext in ("vector", "pg_trgm", "unaccent"):
            c.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext}"))
    Base.metadata.drop_all(motor)
    Base.metadata.create_all(motor)
    yield motor
    motor.dispose()


@pytest.fixture
def bd(motor_pruebas):
    """Sesión limpia en cada test: se vacían las tablas de usuarios al terminar."""
    Fabrica = sessionmaker(bind=motor_pruebas, autoflush=False, expire_on_commit=False)

    def obtener():
        s = Fabrica()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[obtener_sesion] = obtener
    yield Fabrica
    app.dependency_overrides.pop(obtener_sesion, None)
    with motor_pruebas.begin() as c:
        c.execute(text("TRUNCATE usuario, competencia CASCADE"))
