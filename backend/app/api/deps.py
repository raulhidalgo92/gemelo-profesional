# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Dependencias comunes de los endpoints."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.servicios.cuentas import usuario_de_sesion
from gemelo_core.db import FabricaSesiones
from gemelo_core.ia import ClienteIA, ErrorIA, cliente_ia
from gemelo_core.modelos import Usuario

COOKIE_SESION = "gemelo_sesion"


def obtener_sesion() -> Iterator[Session]:
    s = FabricaSesiones()
    try:
        yield s
    finally:
        s.close()


def obtener_cliente_ia() -> ClienteIA | None:
    """Cliente de IA, o None si no está configurado (los endpoints deben degradarse)."""
    try:
        return cliente_ia()
    except ErrorIA:
        return None


SesionDB = Annotated[Session, Depends(obtener_sesion)]
IA = Annotated[ClienteIA | None, Depends(obtener_cliente_ia)]


def usuario_actual(
    s: SesionDB, token: Annotated[str | None, Cookie(alias=COOKIE_SESION)] = None
) -> Usuario:
    """Usuario de la sesión, o 401 si no hay sesión válida."""
    usuario = usuario_de_sesion(s, token) if token else None
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "sin_sesion")
    return usuario


UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]
