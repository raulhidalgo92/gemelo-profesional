# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Registro en dos pasos, activación por código o enlace y sesiones.

1. El usuario envía nombre, correo y contraseña, y acepta la política de privacidad.
2. Recibe un correo con un código de 6 cifras y un enlace; cualquiera de los dos activa la
   cuenta. El código sirve aunque el correo se lea en otro dispositivo.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.servicios import seguridad
from gemelo_core.config import ajustes
from gemelo_core.modelos import CodigoVerificacion, Gemelo, SesionUsuario, Usuario

VALIDEZ_CODIGO = timedelta(minutes=15)
ESPERA_REENVIO = timedelta(seconds=60)
MAX_INTENTOS = 5


class ErrorCuenta(Exception):
    """Error con un código estable que el frontend traduce a un mensaje."""

    def __init__(self, codigo: str, espera: int | None = None):
        super().__init__(codigo)
        self.codigo, self.espera = codigo, espera


@dataclass
class Activacion:
    """Lo que hay que enviar por correo: nunca se guarda en claro."""

    codigo: str
    token: str


def ahora() -> datetime:
    return datetime.now(UTC)


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def buscar(s: Session, email: str) -> Usuario | None:
    return s.scalar(select(Usuario).where(Usuario.email == normalizar_email(email)))


def emitir_codigo(s: Session, usuario: Usuario, proposito: str = "activacion") -> Activacion:
    """Genera un código y un enlace nuevos (invalida los anteriores)."""
    activacion = Activacion(seguridad.nuevo_codigo(), seguridad.nuevo_token())
    s.execute(delete(CodigoVerificacion).where(CodigoVerificacion.usuario_id == usuario.id))
    s.add(
        CodigoVerificacion(
            usuario_id=usuario.id,
            hash_codigo=seguridad.resumen(f"{usuario.id}:{activacion.codigo}"),
            hash_enlace=seguridad.resumen(activacion.token),
            intentos=0,
            expira_en=ahora() + VALIDEZ_CODIGO,
            enviado_en=ahora(),
            proposito=proposito,
        )
    )
    return activacion


def emitir_activacion(s: Session, usuario: Usuario) -> Activacion:
    return emitir_codigo(s, usuario, "activacion")


def registrar(
    s: Session, nombre: str, email: str, contrasena: str
) -> tuple[Usuario, Activacion | None]:
    """Crea la cuenta (o actualiza una sin activar). Si ya estaba activa, no hay activación."""
    usuario = buscar(s, email)
    if usuario is not None and usuario.verificado_en is not None:
        return usuario, None
    if usuario is None:
        usuario = Usuario(email=normalizar_email(email))
        s.add(usuario)
    usuario.nombre = nombre.strip()
    usuario.hash_contrasena = seguridad.hash_contrasena(contrasena)
    usuario.consentimiento_en = ahora()
    usuario.consentimiento_version = ajustes().consentimiento_version
    s.flush()
    return usuario, emitir_activacion(s, usuario)


def reenviar(s: Session, email: str) -> tuple[Usuario, Activacion] | None:
    """Nueva activación si la cuenta existe, no está activa y ha pasado la espera mínima."""
    usuario = buscar(s, email)
    if usuario is None or usuario.verificado_en is not None:
        return None
    previo = s.get(CodigoVerificacion, usuario.id)
    if previo is not None:
        restante = previo.enviado_en + ESPERA_REENVIO - ahora()
        if restante.total_seconds() > 0:
            raise ErrorCuenta("espera", espera=int(restante.total_seconds()) + 1)
    return usuario, emitir_activacion(s, usuario)


def _activar(s: Session, usuario: Usuario) -> Usuario:
    usuario.verificado_en = ahora()
    s.execute(delete(CodigoVerificacion).where(CodigoVerificacion.usuario_id == usuario.id))
    if s.scalar(select(Gemelo.id).where(Gemelo.usuario_id == usuario.id)) is None:
        s.add(Gemelo(usuario_id=usuario.id))
    return usuario


def _comprobar_codigo(s: Session, email: str, codigo: str, proposito: str) -> Usuario:
    """Usuario cuyo código pendiente coincide; cuenta los intentos fallidos."""
    usuario = buscar(s, email)
    pendiente = s.get(CodigoVerificacion, usuario.id) if usuario else None
    if usuario is None or pendiente is None or pendiente.proposito != proposito:
        raise ErrorCuenta("codigo_incorrecto")
    if pendiente.expira_en < ahora():
        raise ErrorCuenta("codigo_caducado")
    if pendiente.intentos >= MAX_INTENTOS:
        raise ErrorCuenta("demasiados_intentos")
    if not seguridad.iguales(
        pendiente.hash_codigo, seguridad.resumen(f"{usuario.id}:{codigo.strip()}")
    ):
        pendiente.intentos += 1
        s.commit()
        raise ErrorCuenta("codigo_incorrecto")
    return usuario


def _usuario_del_enlace(s: Session, token: str, proposito: str) -> Usuario:
    pendiente = s.scalar(
        select(CodigoVerificacion).where(CodigoVerificacion.hash_enlace == seguridad.resumen(token))
    )
    if pendiente is None or pendiente.proposito != proposito or pendiente.expira_en < ahora():
        raise ErrorCuenta("enlace_no_valido")
    return s.get(Usuario, pendiente.usuario_id)


def verificar_codigo(s: Session, email: str, codigo: str) -> Usuario:
    return _activar(s, _comprobar_codigo(s, email, codigo, "activacion"))


def verificar_enlace(s: Session, token: str) -> Usuario:
    return _activar(s, _usuario_del_enlace(s, token, "activacion"))


def pedir_recuperacion(s: Session, email: str) -> tuple[Usuario, Activacion] | None:
    """Código para cambiar la contraseña, solo si la cuenta existe y está activa.
    Si se pidió otro hace menos de un minuto, no se envía nada (sin revelar si existe)."""
    usuario = buscar(s, email)
    if usuario is None or usuario.verificado_en is None:
        return None
    previo = s.get(CodigoVerificacion, usuario.id)
    if previo is not None and previo.enviado_en + ESPERA_REENVIO > ahora():
        return None
    return usuario, emitir_codigo(s, usuario, "recuperacion")


def restablecer(
    s: Session,
    nueva: str,
    *,
    email: str | None = None,
    codigo: str | None = None,
    token: str | None = None,
) -> Usuario:
    """Cambia la contraseña con el código o con el enlace del correo y cierra todas las
    sesiones: si alguien más tenía acceso, deja de tenerlo."""
    if token:
        usuario = _usuario_del_enlace(s, token, "recuperacion")
    else:
        usuario = _comprobar_codigo(s, email or "", codigo or "", "recuperacion")
    usuario.hash_contrasena = seguridad.hash_contrasena(nueva)
    s.execute(delete(CodigoVerificacion).where(CodigoVerificacion.usuario_id == usuario.id))
    s.execute(delete(SesionUsuario).where(SesionUsuario.usuario_id == usuario.id))
    return usuario


def autenticar(s: Session, email: str, contrasena: str) -> Usuario:
    usuario = buscar(s, email)
    hash_guardado = usuario.hash_contrasena if usuario else None
    if not seguridad.verificar_contrasena(contrasena, hash_guardado):
        raise ErrorCuenta("credenciales")
    if usuario.verificado_en is None:
        raise ErrorCuenta("cuenta_no_verificada")
    return usuario


def abrir_sesion(s: Session, usuario: Usuario) -> str:
    token = seguridad.nuevo_token()
    s.add(
        SesionUsuario(
            hash_token=seguridad.resumen(token),
            usuario_id=usuario.id,
            expira_en=ahora() + timedelta(days=ajustes().sesion_dias),
        )
    )
    return token


def usuario_de_sesion(s: Session, token: str) -> Usuario | None:
    sesion = s.get(SesionUsuario, seguridad.resumen(token))
    if sesion is None or sesion.expira_en < ahora():
        return None
    return s.get(Usuario, sesion.usuario_id)


def cerrar_sesion(s: Session, token: str) -> None:
    s.execute(delete(SesionUsuario).where(SesionUsuario.hash_token == seguridad.resumen(token)))


def otras_sesiones(s: Session, usuario: Usuario, token: str | None) -> int:
    """Sesiones abiertas en otros dispositivos (sin contar la actual)."""
    return s.scalar(
        select(func.count()).where(
            SesionUsuario.usuario_id == usuario.id,
            SesionUsuario.hash_token != seguridad.resumen(token or ""),
            SesionUsuario.expira_en > ahora(),
        )
    )


def cerrar_otras_sesiones(s: Session, usuario: Usuario, token: str | None) -> None:
    s.execute(
        delete(SesionUsuario).where(
            SesionUsuario.usuario_id == usuario.id,
            SesionUsuario.hash_token != seguridad.resumen(token or ""),
        )
    )


def cambiar_contrasena(
    s: Session, usuario: Usuario, actual: str, nueva: str, token: str | None
) -> None:
    """Pide la contraseña actual y, por seguridad, cierra las sesiones de otros dispositivos."""
    if not seguridad.verificar_contrasena(actual, usuario.hash_contrasena):
        raise ErrorCuenta("contrasena_actual")
    usuario.hash_contrasena = seguridad.hash_contrasena(nueva)
    cerrar_otras_sesiones(s, usuario, token)
