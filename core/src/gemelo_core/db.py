# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Conexión a PostgreSQL y sesiones de SQLAlchemy."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from gemelo_core.config import ajustes

motor = create_engine(ajustes().database_url, pool_pre_ping=True)
FabricaSesiones = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


@contextmanager
def sesion() -> Iterator[Session]:
    """Sesión transaccional: confirma al salir o deshace si hay error."""
    s = FabricaSesiones()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
