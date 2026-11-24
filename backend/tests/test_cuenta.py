# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
import re
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.api import cuenta
from app.main import app
from app.servicios import correo
from app.servicios.cuentas import ahora
from gemelo_core.modelos import CodigoVerificacion, Usuario

CSRF = {"X-Requested-With": "gemelo"}
DATOS = {
    "nombre": "Ana",
    "email": "Ana@Ejemplo.com",
    "contrasena": "una-clave-larga",
    "acepta_privacidad": True,
}


@pytest.fixture
def correos(monkeypatch):
    enviados = []
    monkeypatch.setattr(correo, "enviar", enviados.append)
    cuenta.limite_registro.reiniciar()
    cuenta.limite_entrada.reiniciar()
    return enviados


@pytest.fixture
def cliente(bd, correos):
    return TestClient(app, headers=CSRF)


def codigo_de(msg) -> str:
    return msg["Subject"][:6]


def token_de(msg) -> str:
    texto = msg.get_body(("plain",)).get_content()
    return re.search(r"token=([\w-]+)", texto).group(1)


def registrar(cliente, correos, **cambios):
    r = cliente.post("/api/cuenta/registro", json={**DATOS, **cambios})
    assert r.status_code == 202
    return correos[-1]


def test_registro_y_activacion_con_codigo(cliente, correos, bd):
    msg = registrar(cliente, correos)
    assert msg["To"] == "ana@ejemplo.com"
    assert "Activar mi cuenta" in msg.get_body(("html",)).get_content()

    r = cliente.post(
        "/api/cuenta/verificar", json={"email": DATOS["email"], "codigo": codigo_de(msg)}
    )
    assert r.status_code == 200
    assert r.json() == {
        "nombre": "Ana",
        "email": "ana@ejemplo.com",
        "avatar": None,
        "bienvenida_pendiente": True,
    }
    assert "httponly" in r.headers["set-cookie"].lower()

    assert cliente.get("/api/cuenta/yo").json()["nombre"] == "Ana"
    with bd() as s:
        usuario = s.query(Usuario).one()
        assert usuario.verificado_en and usuario.consentimiento_version
        assert usuario.gemelo is not None
        assert s.query(CodigoVerificacion).count() == 0


def test_activacion_con_enlace(cliente, correos):
    msg = registrar(cliente, correos)
    r = cliente.post("/api/cuenta/verificar-enlace", json={"token": token_de(msg)})
    assert r.status_code == 200
    assert cliente.post("/api/cuenta/verificar-enlace", json={"token": token_de(msg)}).json() == {
        "detail": "enlace_no_valido"
    }


def test_codigo_incorrecto_y_limite_de_intentos(cliente, correos):
    msg = registrar(cliente, correos)
    malo = "000000" if codigo_de(msg) != "000000" else "111111"
    for _ in range(5):
        r = cliente.post("/api/cuenta/verificar", json={"email": DATOS["email"], "codigo": malo})
        assert r.json()["detail"] == "codigo_incorrecto"
    r = cliente.post(
        "/api/cuenta/verificar", json={"email": DATOS["email"], "codigo": codigo_de(msg)}
    )
    assert r.status_code == 429
    assert r.json()["detail"] == "demasiados_intentos"


def test_codigo_caducado(cliente, correos, bd):
    msg = registrar(cliente, correos)
    with bd() as s:
        s.query(CodigoVerificacion).update({"expira_en": ahora() - timedelta(minutes=1)})
        s.commit()
    r = cliente.post(
        "/api/cuenta/verificar", json={"email": DATOS["email"], "codigo": codigo_de(msg)}
    )
    assert r.json()["detail"] == "codigo_caducado"


def test_reenvio_con_espera_minima(cliente, correos, bd):
    registrar(cliente, correos)
    r = cliente.post("/api/cuenta/reenviar", json={"email": DATOS["email"]})
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0
    with bd() as s:
        s.query(CodigoVerificacion).update({"enviado_en": ahora() - timedelta(minutes=2)})
        s.commit()
    assert cliente.post("/api/cuenta/reenviar", json={"email": DATOS["email"]}).status_code == 202
    assert len(correos) == 2


def test_registro_con_correo_ya_activo_no_revela_nada(cliente, correos):
    msg = registrar(cliente, correos)
    cliente.post("/api/cuenta/verificar", json={"email": DATOS["email"], "codigo": codigo_de(msg)})

    aviso = registrar(cliente, correos, contrasena="otra-clave-distinta")
    assert aviso["Subject"] == "Ya tienes una cuenta"
    # La contraseña no cambia
    entrar = {"email": DATOS["email"], "contrasena": DATOS["contrasena"]}
    assert cliente.post("/api/cuenta/entrar", json=entrar).status_code == 200


def test_entrar(cliente, correos):
    msg = registrar(cliente, correos)
    entrar = {"email": "ana@ejemplo.com", "contrasena": DATOS["contrasena"]}
    r = cliente.post("/api/cuenta/entrar", json=entrar)
    assert (r.status_code, r.json()["detail"]) == (403, "cuenta_no_verificada")

    cliente.post("/api/cuenta/verificar", json={"email": DATOS["email"], "codigo": codigo_de(msg)})
    cliente.cookies.clear()
    malo = {**entrar, "contrasena": "no-es-la-clave"}
    assert cliente.post("/api/cuenta/entrar", json=malo).status_code == 401
    assert cliente.post("/api/cuenta/entrar", json=entrar).status_code == 200
    assert cliente.get("/api/cuenta/yo").status_code == 200


def test_salir_cierra_la_sesion(cliente, correos):
    msg = registrar(cliente, correos)
    cliente.post("/api/cuenta/verificar", json={"email": DATOS["email"], "codigo": codigo_de(msg)})
    token = cliente.cookies.get("gemelo_sesion")
    assert cliente.post("/api/cuenta/salir").status_code == 204
    cliente.cookies.set("gemelo_sesion", token, path="/api")
    assert cliente.get("/api/cuenta/yo").status_code == 401


def test_bienvenida_y_baja_de_la_cuenta(cliente, correos, bd):
    msg = registrar(cliente, correos)
    cliente.post("/api/cuenta/verificar", json={"email": DATOS["email"], "codigo": codigo_de(msg)})
    assert cliente.post("/api/cuenta/bienvenida").status_code == 204
    assert cliente.get("/api/cuenta/yo").json()["bienvenida_pendiente"] is False

    malo = cliente.request("DELETE", "/api/cuenta", json={"contrasena": "no-es-la-clave"})
    assert (malo.status_code, malo.json()["detail"]) == (400, "contrasena_incorrecta")
    r = cliente.request("DELETE", "/api/cuenta", json={"contrasena": DATOS["contrasena"]})
    assert r.status_code == 204
    with bd() as s:
        assert s.query(Usuario).count() == 0


@pytest.mark.parametrize(
    "cambio",
    [{"contrasena": "corta"}, {"acepta_privacidad": False}, {"email": "no-es-un-correo"}],
)
def test_datos_de_registro_no_validos(cliente, cambio):
    assert cliente.post("/api/cuenta/registro", json={**DATOS, **cambio}).status_code == 422


def test_sin_cabecera_csrf_se_rechaza(bd):
    r = TestClient(app).post("/api/cuenta/registro", json=DATOS)
    assert (r.status_code, r.json()["detail"]) == (403, "falta_cabecera_csrf")


def activa(cliente, correos) -> TestClient:
    """Cuenta activada con sesión en `cliente` y otra sesión en un segundo dispositivo."""
    msg = registrar(cliente, correos)
    cliente.post("/api/cuenta/verificar", json={"email": DATOS["email"], "codigo": codigo_de(msg)})
    otro = TestClient(app, headers=CSRF)
    entrar = {"email": DATOS["email"], "contrasena": DATOS["contrasena"]}
    assert otro.post("/api/cuenta/entrar", json=entrar).status_code == 200
    return otro


def test_detalle_y_cambio_de_nombre(cliente, correos):
    activa(cliente, correos)
    cuenta_ = cliente.get("/api/cuenta").json()
    assert (cuenta_["email"], cuenta_["otras_sesiones"]) == ("ana@ejemplo.com", 1)
    assert cuenta_["verificada_en"] and cuenta_["consentimiento_version"]

    r = cliente.patch("/api/cuenta", json={"nombre": "  Ana María "})
    assert r.json()["nombre"] == "Ana María"
    assert cliente.patch("/api/cuenta", json={"nombre": "   "}).status_code == 422
    # El correo no se puede cambiar
    cliente.patch("/api/cuenta", json={"nombre": "Ana", "email": "otro@ejemplo.com"})
    assert cliente.get("/api/cuenta/yo").json()["email"] == "ana@ejemplo.com"


def test_elegir_avatar(cliente, correos):
    activa(cliente, correos)
    assert cliente.get("/api/cuenta/yo").json()["avatar"] is None
    r = cliente.patch("/api/cuenta", json={"avatar": "luna"})
    # Cambiar el avatar no toca el nombre
    assert (r.json()["avatar"], r.json()["nombre"]) == ("luna", "Ana")
    assert cliente.patch("/api/cuenta", json={"avatar": "foto.jpg"}).status_code == 422
    # Cambiar el nombre no toca el avatar; null vuelve a la inicial
    assert cliente.patch("/api/cuenta", json={"nombre": "Ana"}).json()["avatar"] == "luna"
    assert cliente.patch("/api/cuenta", json={"avatar": None}).json()["avatar"] is None


def test_cambiar_contrasena_cierra_las_demas_sesiones(cliente, correos):
    otro = activa(cliente, correos)
    nueva = {"actual": "no-es-la-clave", "nueva": "otra-clave-larga"}
    r = cliente.post("/api/cuenta/contrasena", json=nueva)
    assert (r.status_code, r.json()["detail"]) == (400, "contrasena_actual")
    corta = {"actual": DATOS["contrasena"], "nueva": "corta"}
    assert cliente.post("/api/cuenta/contrasena", json=corta).status_code == 422

    nueva["actual"] = DATOS["contrasena"]
    assert cliente.post("/api/cuenta/contrasena", json=nueva).status_code == 204
    assert cliente.get("/api/cuenta/yo").status_code == 200
    assert otro.get("/api/cuenta/yo").status_code == 401
    entrar = {"email": DATOS["email"], "contrasena": "otra-clave-larga"}
    assert otro.post("/api/cuenta/entrar", json=entrar).status_code == 200


def test_cerrar_las_demas_sesiones(cliente, correos):
    otro = activa(cliente, correos)
    assert cliente.post("/api/cuenta/cerrar-sesiones").status_code == 204
    assert cliente.get("/api/cuenta").json()["otras_sesiones"] == 0
    assert cliente.get("/api/cuenta/yo").status_code == 200
    assert otro.get("/api/cuenta/yo").status_code == 401


def test_descargar_mis_datos(cliente, correos, bd):
    activa(cliente, correos)
    r = cliente.get("/api/cuenta/exportar")
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    datos = r.json()
    assert datos["cuenta"]["email"] == "ana@ejemplo.com"
    assert (datos["gemelo"]["competencias"], datos["gemelo"]["evidencias"]) == ([], [])
    # Nunca salen los secretos
    assert "hash" not in r.text
    assert TestClient(app).get("/api/cuenta/exportar").status_code == 401


def test_recuperar_no_revela_si_la_cuenta_existe(cliente, correos):
    r = cliente.post("/api/cuenta/recuperar", json={"email": "nadie@ejemplo.com"})
    assert r.status_code == 202
    assert correos == []
    # Una cuenta sin activar tampoco recibe nada (su camino es la activación)
    registrar(cliente, correos)
    enviados = len(correos)
    r2 = cliente.post("/api/cuenta/recuperar", json={"email": DATOS["email"]})
    assert (r2.status_code, r2.json()) == (202, r.json())
    assert len(correos) == enviados


def test_recuperar_con_codigo_cambia_la_contrasena_y_entra(cliente, correos):
    otro = activa(cliente, correos)
    anonimo = TestClient(app, headers=CSRF)
    anonimo.post("/api/cuenta/recuperar", json={"email": DATOS["email"]})
    msg = correos[-1]
    assert "cambiar tu contraseña" in msg["Subject"]
    # Pedirlo otra vez enseguida no envía otro correo
    anonimo.post("/api/cuenta/recuperar", json={"email": DATOS["email"]})
    assert correos[-1] is msg

    nueva = {"email": DATOS["email"], "contrasena": "otra-clave-larga"}
    r = anonimo.post("/api/cuenta/restablecer", json={**nueva, "codigo": "000000"})
    assert (r.status_code, r.json()["detail"]) == (400, "codigo_incorrecto")
    r = anonimo.post("/api/cuenta/restablecer", json={**nueva, "codigo": codigo_de(msg)})
    assert r.status_code == 200 and r.json()["email"] == "ana@ejemplo.com"
    # Entra directamente; las demás sesiones se cierran
    assert anonimo.get("/api/cuenta/yo").status_code == 200
    assert otro.get("/api/cuenta/yo").status_code == 401
    assert cliente.get("/api/cuenta/yo").status_code == 401
    entrar = {"email": DATOS["email"], "contrasena": "otra-clave-larga"}
    assert TestClient(app, headers=CSRF).post("/api/cuenta/entrar", json=entrar).status_code == 200
    # El código ya no sirve una segunda vez
    r = anonimo.post("/api/cuenta/restablecer", json={**nueva, "codigo": codigo_de(msg)})
    assert r.status_code == 400


def test_recuperar_con_enlace_y_sin_mezclar_enlaces(cliente, correos):
    msg_activacion = registrar(cliente, correos)
    # Un enlace de activación no sirve para cambiar la contraseña
    nueva = {"contrasena": "otra-clave-larga", "token": token_de(msg_activacion)}
    r = cliente.post("/api/cuenta/restablecer", json=nueva)
    assert (r.status_code, r.json()["detail"]) == (400, "enlace_no_valido")
    cliente.post("/api/cuenta/verificar-enlace", json={"token": token_de(msg_activacion)})

    cliente.post("/api/cuenta/recuperar", json={"email": DATOS["email"]})
    token = token_de(correos[-1])
    assert "/restablecer?token=" in correos[-1].get_body(("plain",)).get_content()
    # …ni un enlace de recuperación para activar
    r = cliente.post("/api/cuenta/verificar-enlace", json={"token": token})
    assert r.json()["detail"] == "enlace_no_valido"
    r = cliente.post(
        "/api/cuenta/restablecer", json={"contrasena": "otra-clave-larga", "token": token}
    )
    assert r.status_code == 200


@pytest.mark.parametrize(
    "datos",
    [
        {"contrasena": "otra-clave-larga"},
        {"contrasena": "otra-clave-larga", "email": "ana@ejemplo.com"},
        {"contrasena": "corta", "email": "ana@ejemplo.com", "codigo": "123456"},
    ],
)
def test_restablecer_datos_no_validos(cliente, datos):
    assert cliente.post("/api/cuenta/restablecer", json=datos).status_code == 422
