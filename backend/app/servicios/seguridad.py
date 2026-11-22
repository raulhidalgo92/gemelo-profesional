# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Contraseñas, tokens y límites de intentos.

Las contraseñas se guardan con argon2id. Los códigos, enlaces y sesiones se guardan como
HMAC con la clave secreta del servidor: quien obtenga una copia de la base de datos no
puede usarlos ni averiguar los códigos de 6 cifras probando todas las combinaciones.
"""

import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque

from pwdlib import PasswordHash

from gemelo_core.config import ajustes

_hasher = PasswordHash.recommended()
# Hash de referencia para tardar lo mismo cuando el correo no existe
_HASH_FICTICIO = _hasher.hash(secrets.token_urlsafe(16))


def hash_contrasena(contrasena: str) -> str:
    return _hasher.hash(contrasena)


def verificar_contrasena(contrasena: str, hash_guardado: str | None) -> bool:
    if hash_guardado is None:
        _hasher.verify(contrasena, _HASH_FICTICIO)
        return False
    return _hasher.verify(contrasena, hash_guardado)


def resumen(valor: str) -> str:
    clave = ajustes().secret_key.encode()
    return hmac.new(clave, valor.encode(), hashlib.sha256).hexdigest()


def iguales(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def nuevo_token() -> str:
    return secrets.token_urlsafe(32)


def nuevo_codigo() -> str:
    return f"{secrets.randbelow(10**6):06d}"


class Limitador:
    """Máximo de peticiones por clave (IP, correo…) en una ventana de tiempo, en memoria."""

    def __init__(self, maximo: int, segundos: int):
        self.maximo, self.segundos = maximo, segundos
        self._marcas: dict[str, deque[float]] = defaultdict(deque)

    def permitir(self, clave: str) -> bool:
        ahora = time.monotonic()
        marcas = self._marcas[clave]
        while marcas and ahora - marcas[0] > self.segundos:
            marcas.popleft()
        if len(marcas) >= self.maximo:
            return False
        marcas.append(ahora)
        return True

    def reiniciar(self) -> None:
        self._marcas.clear()
