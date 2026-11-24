# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Registro, activación, sesiones y gestión de la cuenta: nombre, contraseña,
descarga de los datos y baja (RGPD)."""

import json
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Cookie, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.api.deps import COOKIE_SESION, SesionDB, UsuarioActual
from app.servicios import correo, cuentas, exportacion, seguridad
from app.servicios.cuentas import ErrorCuenta
from gemelo_core.config import ajustes
from gemelo_core.modelos import Usuario

router = APIRouter()

# Límites por IP (en memoria; suficientes para un único proceso)
limite_registro = seguridad.Limitador(maximo=10, segundos=3600)
limite_entrada = seguridad.Limitador(maximo=10, segundos=900)

TokenSesion = Annotated[str | None, Cookie(alias=COOKIE_SESION)]


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


# Avatares de la colección de la app (los dibuja el frontend). Nunca se guardan fotos:
# no hacen falta para nada y serían un dato personal más (minimización, RGPD)
Avatar = Literal["gemelo", "lila", "montana", "sol", "ola", "luna", "rombo", "brote"]


class UsuarioSalida(BaseModel):
    nombre: str
    email: str
    avatar: str | None
    bienvenida_pendiente: bool

    @classmethod
    def de(cls, u: Usuario) -> "UsuarioSalida":
        return cls(
            nombre=u.nombre,
            email=u.email,
            avatar=u.avatar,
            bienvenida_pendiente=u.bienvenida_en is None,
        )


class CuentaSalida(BaseModel):
    nombre: str
    email: str
    verificada_en: datetime | None
    consentimiento_en: datetime | None
    consentimiento_version: str | None
    # Sesiones abiertas en otros dispositivos
    otras_sesiones: int


class PerfilEntrada(BaseModel):
    """Cambios del perfil; solo se tocan los campos que llegan."""

    nombre: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)] | None
    ) = None
    # null: volver a la inicial
    avatar: Avatar | None = None


class ContrasenaEntrada(BaseModel):
    actual: str = Field(max_length=128)
    nueva: str = Field(min_length=10, max_length=128)


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
    token: TokenSesion = None,
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


@router.get("")
def detalle(usuario: UsuarioActual, s: SesionDB, token: TokenSesion = None) -> CuentaSalida:
    return CuentaSalida(
        nombre=usuario.nombre,
        email=usuario.email,
        verificada_en=usuario.verificado_en,
        consentimiento_en=usuario.consentimiento_en,
        consentimiento_version=usuario.consentimiento_version,
        otras_sesiones=cuentas.otras_sesiones(s, usuario, token),
    )


@router.patch("")
def cambiar_perfil(datos: PerfilEntrada, usuario: UsuarioActual, s: SesionDB) -> UsuarioSalida:
    """Nombre y avatar. El correo no se puede cambiar: identifica la cuenta."""
    if datos.nombre is not None:
        usuario.nombre = datos.nombre
    if "avatar" in datos.model_fields_set:
        usuario.avatar = datos.avatar
    s.commit()
    return UsuarioSalida.de(usuario)


@router.post("/contrasena", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_contrasena(
    datos: ContrasenaEntrada,
    usuario: UsuarioActual,
    s: SesionDB,
    request: Request,
    token: TokenSesion = None,
) -> None:
    _limitar(limite_entrada, request)
    try:
        cuentas.cambiar_contrasena(s, usuario, datos.actual, datos.nueva, token)
    except ErrorCuenta as e:
        raise _error(e) from e
    s.commit()


@router.post("/cerrar-sesiones", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_sesiones(usuario: UsuarioActual, s: SesionDB, token: TokenSesion = None) -> None:
    """Cierra la sesión en los demás dispositivos; la actual sigue abierta."""
    cuentas.cerrar_otras_sesiones(s, usuario, token)
    s.commit()


@router.get("/exportar")
def exportar(usuario: UsuarioActual, s: SesionDB) -> Response:
    """Descarga de todos los datos del usuario en JSON (derecho de acceso y portabilidad)."""
    contenido = json.dumps(exportacion.exportar(s, usuario), ensure_ascii=False, indent=2)
    return Response(
        contenido,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="mis-datos-gemelo.json"',
            "Cache-Control": "no-store",
        },
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def baja(datos: BajaEntrada, usuario: UsuarioActual, s: SesionDB, respuesta: Response) -> None:
    """Elimina la cuenta y, en cascada, el gemelo y todos sus datos (RGPD)."""
    if not seguridad.verificar_contrasena(datos.contrasena, usuario.hash_contrasena):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "contrasena_incorrecta")
    s.delete(usuario)
    s.commit()
    respuesta.delete_cookie(COOKIE_SESION, path="/api")
