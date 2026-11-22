# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Registro, activación, inicio y cierre de sesión, y baja de la cuenta (RGPD)."""

from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Cookie, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import COOKIE_SESION, SesionDB, UsuarioActual
from app.servicios import correo, cuentas, seguridad
from app.servicios.cuentas import ErrorCuenta
from gemelo_core.config import ajustes
from gemelo_core.modelos import Usuario

router = APIRouter()

# Límites por IP (en memoria; suficientes para un único proceso)
limite_registro = seguridad.Limitador(maximo=10, segundos=3600)
limite_entrada = seguridad.Limitador(maximo=10, segundos=900)


class RegistroEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    email: EmailStr
    contrasena: str = Field(min_length=10, max_length=128)
    acepta_privacidad: Literal[True]


class EmailEntrada(BaseModel):
    email: EmailStr


class CodigoEntrada(BaseModel):
    email: EmailStr
    codigo: str = Field(pattern=r"^\s*\d{6}\s*$")


class EnlaceEntrada(BaseModel):
    token: str = Field(min_length=20, max_length=100)


class EntradaSesion(BaseModel):
    email: EmailStr
    contrasena: str = Field(max_length=128)


class BajaEntrada(BaseModel):
    contrasena: str = Field(max_length=128)


class UsuarioSalida(BaseModel):
    nombre: str
    email: str
    bienvenida_pendiente: bool

    @classmethod
    def de(cls, u: Usuario) -> "UsuarioSalida":
        return cls(nombre=u.nombre, email=u.email, bienvenida_pendiente=u.bienvenida_en is None)


class Aviso(BaseModel):
    detalle: str


def _error(e: ErrorCuenta) -> HTTPException:
    estados = {
        "credenciales": status.HTTP_401_UNAUTHORIZED,
        "cuenta_no_verificada": status.HTTP_403_FORBIDDEN,
        "espera": status.HTTP_429_TOO_MANY_REQUESTS,
        "demasiados_intentos": status.HTTP_429_TOO_MANY_REQUESTS,
    }
    cabeceras = {"Retry-After": str(e.espera)} if e.espera else None
    return HTTPException(estados.get(e.codigo, status.HTTP_400_BAD_REQUEST), e.codigo, cabeceras)


def _limitar(limitador: seguridad.Limitador, request: Request) -> None:
    ip = request.client.host if request.client else "desconocida"
    if not limitador.permitir(ip):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "demasiadas_peticiones")


def _enviar_activacion(tareas: BackgroundTasks, usuario: Usuario, act: cuentas.Activacion):
    enlace = f"{ajustes().url_publica}/verificar?token={act.token}"
    msg = correo.componer(
        usuario.email,
        f"{act.codigo} es tu código para activar tu cuenta",
        "activacion",
        nombre=usuario.nombre,
        codigo=act.codigo,
        enlace=enlace,
        minutos=int(cuentas.VALIDEZ_CODIGO.total_seconds() // 60),
    )
    tareas.add_task(correo.enviar, msg)


def _con_sesion(s: SesionDB, respuesta: Response, usuario: Usuario) -> UsuarioSalida:
    token = cuentas.abrir_sesion(s, usuario)
    s.commit()
    respuesta.set_cookie(
        COOKIE_SESION,
        token,
        max_age=ajustes().sesion_dias * 86400,
        httponly=True,
        secure=ajustes().cookie_segura,
        samesite="lax",
        path="/api",
    )
    return UsuarioSalida.de(usuario)


RESPUESTA_REGISTRO = "Si los datos son correctos, recibirás un correo para activar la cuenta."


@router.post("/registro", status_code=status.HTTP_202_ACCEPTED)
def registro(
    datos: RegistroEntrada, s: SesionDB, tareas: BackgroundTasks, request: Request
) -> Aviso:
    """Paso 1. La respuesta es siempre la misma, exista o no la cuenta."""
    _limitar(limite_registro, request)
    usuario, activacion = cuentas.registrar(s, datos.nombre, datos.email, datos.contrasena)
    s.commit()
    if activacion:
        _enviar_activacion(tareas, usuario, activacion)
    else:  # ya tenía cuenta: se le avisa a él, no a quien rellena el formulario
        msg = correo.componer(
            usuario.email, "Ya tienes una cuenta", "cuenta_existente", nombre=usuario.nombre
        )
        tareas.add_task(correo.enviar, msg)
    return Aviso(detalle=RESPUESTA_REGISTRO)


@router.post("/reenviar", status_code=status.HTTP_202_ACCEPTED)
def reenviar(datos: EmailEntrada, s: SesionDB, tareas: BackgroundTasks, request: Request) -> Aviso:
    _limitar(limite_registro, request)
    try:
        resultado = cuentas.reenviar(s, datos.email)
    except ErrorCuenta as e:
        raise _error(e) from e
    s.commit()
    if resultado:
        _enviar_activacion(tareas, *resultado)
    return Aviso(detalle=RESPUESTA_REGISTRO)


@router.post("/verificar")
def verificar(datos: CodigoEntrada, s: SesionDB, respuesta: Response) -> UsuarioSalida:
    """Paso 2 con el código del correo. Activa la cuenta e inicia la sesión."""
    try:
        usuario = cuentas.verificar_codigo(s, datos.email, datos.codigo)
    except ErrorCuenta as e:
        raise _error(e) from e
    return _con_sesion(s, respuesta, usuario)


@router.post("/verificar-enlace")
def verificar_enlace(datos: EnlaceEntrada, s: SesionDB, respuesta: Response) -> UsuarioSalida:
    """Paso 2 con el enlace del correo (la web lo envía por POST para que los filtros de
    correo que abren los enlaces no activen la cuenta por su cuenta)."""
    try:
        usuario = cuentas.verificar_enlace(s, datos.token)
    except ErrorCuenta as e:
        raise _error(e) from e
    return _con_sesion(s, respuesta, usuario)


@router.post("/entrar")
def entrar(
    datos: EntradaSesion, s: SesionDB, respuesta: Response, request: Request
) -> UsuarioSalida:
    _limitar(limite_entrada, request)
    try:
        usuario = cuentas.autenticar(s, datos.email, datos.contrasena)
    except ErrorCuenta as e:
        raise _error(e) from e
    return _con_sesion(s, respuesta, usuario)


@router.post("/salir", status_code=status.HTTP_204_NO_CONTENT)
def salir(
    s: SesionDB,
    respuesta: Response,
    token: Annotated[str | None, Cookie(alias=COOKIE_SESION)] = None,
) -> None:
    if token:
        cuentas.cerrar_sesion(s, token)
        s.commit()
    respuesta.delete_cookie(COOKIE_SESION, path="/api")


@router.get("/yo")
def yo(usuario: UsuarioActual) -> UsuarioSalida:
    return UsuarioSalida.de(usuario)


@router.post("/bienvenida", status_code=status.HTTP_204_NO_CONTENT)
def terminar_bienvenida(usuario: UsuarioActual, s: SesionDB) -> None:
    """El usuario ha terminado o pospuesto el asistente de bienvenida."""
    usuario.bienvenida_en = cuentas.ahora()
    s.commit()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def baja(datos: BajaEntrada, usuario: UsuarioActual, s: SesionDB, respuesta: Response) -> None:
    """Elimina la cuenta y, en cascada, el gemelo y todos sus datos (RGPD)."""
    if not seguridad.verificar_contrasena(datos.contrasena, usuario.hash_contrasena):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "credenciales")
    s.delete(usuario)
    s.commit()
    respuesta.delete_cookie(COOKIE_SESION, path="/api")
