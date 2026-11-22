# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
import io

import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.api.deps import obtener_cliente_ia
from app.main import app
from app.servicios import cv
from gemelo_core.extraccion import CompetenciaDetectada
from gemelo_core.modelos import Competencia, Evidencia, GemeloCompetencia

ESCO = "http://data.europa.eu/esco/skill"
TEXTO_CV = "Ana Pérez Gómez\nana@correo.com · 612345678\n" + "Experiencia en Excel y SQL. " * 10


def docx(texto: str) -> bytes:
    doc = Document()
    for linea in texto.splitlines():
        doc.add_paragraph(linea)
    salida = io.BytesIO()
    doc.save(salida)
    return salida.getvalue()


def test_lee_un_word():
    assert "Excel y SQL" in cv.texto_de_archivo(docx(TEXTO_CV))


@pytest.mark.parametrize(
    ("contenido", "codigo"),
    [
        (b"GIF89a imagen", "formato_no_admitido"),
        (b"%PDF-1.7 roto", "archivo_ilegible"),
        (b"x" * (cv.MAX_BYTES + 1), "archivo_grande"),
    ],
)
def test_rechaza_archivos_no_validos(contenido, codigo):
    with pytest.raises(cv.ErrorCv) as e:
        cv.texto_de_archivo(contenido)
    assert e.value.codigo == codigo


def test_un_cv_casi_vacio_no_se_analiza():
    with pytest.raises(cv.ErrorCv) as e:
        cv.texto_de_archivo(docx("Ana Pérez"))
    assert e.value.codigo == "sin_texto"


def test_oculta_el_nombre_completo_de_la_cabecera():
    assert cv.nombres_a_ocultar(TEXTO_CV, "Ana") == ["Ana Pérez Gómez", "Ana"]
    assert cv.nombres_a_ocultar("Currículum vitae 2026\n...", "Ana") == ["Ana"]


@pytest.fixture
def usuario_con_sesion(bd, monkeypatch):
    """Usuario activado con sesión abierta y una IA simulada."""
    from app.api import cuenta
    from app.servicios import correo

    enviados = []
    monkeypatch.setattr(correo, "enviar", enviados.append)
    cuenta.limite_registro.reiniciar()
    with bd() as s:
        s.add_all(
            [
                Competencia(uri=f"{ESCO}/excel", titulo="utilizar hojas de cálculo"),
                Competencia(uri=f"{ESCO}/sql", titulo="SQL"),
            ]
        )
        s.commit()
    cliente = TestClient(app, headers={"X-Requested-With": "gemelo"})
    datos = {"nombre": "Ana", "email": "ana@ejemplo.com", "contrasena": "una-clave-larga"}
    cliente.post("/api/cuenta/registro", json={**datos, "acepta_privacidad": True})
    codigo = enviados[-1]["Subject"][:6]
    cliente.post("/api/cuenta/verificar", json={"email": datos["email"], "codigo": codigo})

    recibido = {}

    def proponer(ia, texto, cv=False):
        recibido["texto"] = texto
        return ["Excel", "SQL"]

    def asociar(s, ia, terminos, contexto):
        return [
            CompetenciaDetectada(f"{ESCO}/excel", "utilizar hojas de cálculo", "Excel", 0.8),
            CompetenciaDetectada(f"{ESCO}/sql", "SQL", "SQL", 0.9),
        ]

    monkeypatch.setattr(cv, "proponer_terminos", proponer)
    monkeypatch.setattr(cv, "asociar_a_esco", asociar)
    app.dependency_overrides[obtener_cliente_ia] = lambda: object()
    yield cliente, recibido
    app.dependency_overrides.pop(obtener_cliente_ia, None)


def test_subir_cv_guarda_competencias_declaradas_sin_datos_personales(usuario_con_sesion, bd):
    cliente, recibido = usuario_con_sesion
    archivo = {"archivo": ("cv.docx", docx(TEXTO_CV), "application/octet-stream")}
    r = cliente.post("/api/gemelo/cv", files=archivo)
    assert r.status_code == 200
    assert [c["titulo"] for c in r.json()] == ["SQL", "utilizar hojas de cálculo"]
    assert r.json()[1]["origen"] == "Excel"

    # Al modelo de lenguaje no le llegan nombre, correo ni teléfono
    for dato in ("Ana Pérez", "ana@correo.com", "612345678"):
        assert dato not in recibido["texto"]

    with bd() as s:
        assert s.query(GemeloCompetencia).count() == 2
        assert {e.origen for e in s.query(Evidencia)} == {"cv"}

    # El usuario quita una competencia que no reconoce
    cliente.request("DELETE", "/api/gemelo/competencias", params={"uri": f"{ESCO}/sql"})
    assert [c["titulo"] for c in cliente.get("/api/gemelo/competencias").json()] == [
        "utilizar hojas de cálculo"
    ]


def test_archivo_no_admitido(usuario_con_sesion):
    cliente, _ = usuario_con_sesion
    r = cliente.post("/api/gemelo/cv", files={"archivo": ("foto.png", b"\x89PNG", "image/png")})
    assert (r.status_code, r.json()["detail"]) == (422, "formato_no_admitido")


def test_sin_sesion_no_se_puede_subir(bd):
    r = TestClient(app, headers={"X-Requested-With": "gemelo"}).post(
        "/api/gemelo/cv", files={"archivo": ("cv.docx", b"PK", "application/octet-stream")}
    )
    assert r.status_code == 401
