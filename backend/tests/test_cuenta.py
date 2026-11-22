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
    assert r.json() == {"nombre": "Ana", "email": "ana@ejemplo.com", "bienvenida_pendiente": True}
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
    assert malo.status_code == 401
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
