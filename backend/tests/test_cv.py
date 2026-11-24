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
from gemelo_core.modelos import Competencia, Evidencia, Gemelo, GemeloCompetencia
from gemelo_core.trayectoria import PerfilCv

ESCO = "http://data.europa.eu/esco/skill"
PERFIL = PerfilCv(
    resumen="Analista de datos con 5 años de experiencia.",
    experiencias=[{"puesto": "Analista de datos", "sector": "Banca", "inicio": 2021}],
    formacion=[{"titulo": "Grado en Estadística", "inicio": 2016, "fin": 2020}],
    nivel_ingles="B2",
)
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
                Competencia(uri=f"{ESCO}/ingles", titulo="inglés"),
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

    def perfil(ia, texto):
        return PERFIL

    monkeypatch.setattr(cv, "proponer_terminos", proponer)
    monkeypatch.setattr(cv, "asociar_a_esco", asociar)
    monkeypatch.setattr(cv, "extraer_perfil", perfil)
    app.dependency_overrides[obtener_cliente_ia] = lambda: object()
    yield cliente, recibido
    app.dependency_overrides.pop(obtener_cliente_ia, None)


def _analizar(cliente):
    archivo = {"archivo": ("cv.docx", docx(TEXTO_CV), "application/octet-stream")}
    r = cliente.post("/api/gemelo/cv/analizar", files=archivo)
    assert r.status_code == 200
    return r.json()


def test_analizar_no_guarda_nada_ni_envia_datos_personales(usuario_con_sesion, bd):
    cliente, recibido = usuario_con_sesion
    analisis = _analizar(cliente)
    assert [(c["titulo"], c["termino"], c["nueva"]) for c in analisis["competencias"]] == [
        ("utilizar hojas de cálculo", "Excel", True),
        ("SQL", "SQL", True),
    ]
    assert analisis["perfil"]["experiencias"][0]["puesto"] == "Analista de datos"
    assert (analisis["ya_no"], analisis["trayectoria_cambia"]) == ([], True)

    # Al modelo de lenguaje no le llegan nombre, correo ni teléfono
    for dato in ("Ana Pérez", "ana@correo.com", "612345678"):
        assert dato not in recibido["texto"]
    with bd() as s:
        assert s.query(GemeloCompetencia).count() == 0
    assert cliente.get("/api/gemelo").json() == {"perfil": None, "actualizado_en": None}


def test_aplicar_guarda_lo_confirmado(usuario_con_sesion, bd):
    cliente, _ = usuario_con_sesion
    analisis = _analizar(cliente)
    r = cliente.post(
        "/api/gemelo/cv/aplicar",
        json={"perfil": analisis["perfil"], "competencias": analisis["competencias"]},
    )
    assert [c["titulo"] for c in r.json()] == ["SQL", "utilizar hojas de cálculo"]
    assert r.json()[1]["origen"] == "Excel"
    with bd() as s:
        assert {e.origen for e in s.query(Evidencia)} == {"cv"}
    gemelo = cliente.get("/api/gemelo").json()
    assert gemelo["perfil"]["experiencias"][0]["sector"] == "Banca"
    assert gemelo["perfil"]["nivel_ingles"] == "B2"
    assert gemelo["actualizado_en"]

    # Un segundo análisis del mismo CV no trae cambios
    analisis = _analizar(cliente)
    assert not any(c["nueva"] for c in analisis["competencias"])
    assert (analisis["ya_no"], analisis["trayectoria_cambia"]) == ([], False)

    # El usuario quita una competencia que no reconoce
    cliente.request("DELETE", "/api/gemelo/competencias", params={"uri": f"{ESCO}/sql"})
    assert [c["titulo"] for c in cliente.get("/api/gemelo/competencias").json()] == [
        "utilizar hojas de cálculo"
    ]


def test_un_cv_nuevo_respeta_lo_demostrado_y_lo_que_se_conserva(usuario_con_sesion, bd):
    cliente, _ = usuario_con_sesion
    perfil = PERFIL.model_dump()
    excel = {"uri": f"{ESCO}/excel", "termino": "Excel", "similitud": 0.8}
    sql = {"uri": f"{ESCO}/sql", "termino": "SQL", "similitud": 0.9}
    ingles = {"uri": f"{ESCO}/ingles", "termino": "inglés", "similitud": 0.9}
    cliente.post(
        "/api/gemelo/cv/aplicar", json={"perfil": perfil, "competencias": [excel, sql, ingles]}
    )
    with bd() as s:
        s.get(
            GemeloCompetencia, (s.query(Gemelo).one().id, f"{ESCO}/ingles")
        ).nivel_demostrado = 0.8
        s.commit()

    # El CV nuevo solo trae Excel y SQL: inglés está demostrada, así que no se pregunta
    assert _analizar(cliente)["ya_no"] == []

    # Ahora solo trae Excel: SQL ya no aparece y el usuario decide conservarla
    r = cliente.post(
        "/api/gemelo/cv/aplicar",
        json={"perfil": perfil, "competencias": [excel], "conservar": [f"{ESCO}/sql"]},
    )
    origenes = {c["titulo"]: c["origen"] for c in r.json()}
    assert origenes == {"inglés": None, "SQL": "SQL", "utilizar hojas de cálculo": "Excel"}

    # Y en otra actualización deja que se quite
    r = cliente.post("/api/gemelo/cv/aplicar", json={"perfil": perfil, "competencias": [excel]})
    assert {c["titulo"] for c in r.json()} == {"inglés", "utilizar hojas de cálculo"}


def test_aplicar_ignora_competencias_que_no_son_de_esco(usuario_con_sesion):
    cliente, _ = usuario_con_sesion
    falsa = {"uri": "http://ejemplo.com/falsa", "termino": "x", "similitud": 0.5}
    r = cliente.post(
        "/api/gemelo/cv/aplicar", json={"perfil": PERFIL.model_dump(), "competencias": [falsa]}
    )
    assert (r.status_code, r.json()) == (200, [])


def test_anadir_una_competencia_del_catalogo(usuario_con_sesion, bd):
    cliente, _ = usuario_con_sesion
    excel = {"uri": f"{ESCO}/excel", "termino": "Excel", "similitud": 0.8}
    cliente.post(
        "/api/gemelo/cv/aplicar", json={"perfil": PERFIL.model_dump(), "competencias": [excel]}
    )

    r = cliente.post("/api/gemelo/competencias", json={"uri": f"{ESCO}/sql"})
    assert r.status_code == 201
    assert (r.json()["titulo"], r.json()["anadida"], r.json()["origen"]) == ("SQL", True, None)
    # Añadirla otra vez no la duplica
    cliente.post("/api/gemelo/competencias", json={"uri": f"{ESCO}/sql"})
    with bd() as s:
        assert s.query(Evidencia).filter_by(origen="manual").count() == 1

    # Un CV nuevo que no la trae no la quita ni pregunta por ella
    assert _analizar(cliente)["ya_no"] == []
    r = cliente.post(
        "/api/gemelo/cv/aplicar", json={"perfil": PERFIL.model_dump(), "competencias": []}
    )
    assert [c["titulo"] for c in r.json()] == ["SQL"]

    r = cliente.post("/api/gemelo/competencias", json={"uri": "http://ejemplo.com/falsa"})
    assert (r.status_code, r.json()["detail"]) == (404, "competencia_no_encontrada")


def test_archivo_no_admitido(usuario_con_sesion):
    cliente, _ = usuario_con_sesion
    r = cliente.post(
        "/api/gemelo/cv/analizar", files={"archivo": ("foto.png", b"\x89PNG", "image/png")}
    )
    assert (r.status_code, r.json()["detail"]) == (422, "formato_no_admitido")


def test_sin_sesion_no_se_puede_subir(bd):
    r = TestClient(app, headers={"X-Requested-With": "gemelo"}).post(
        "/api/gemelo/cv/analizar", files={"archivo": ("cv.docx", b"PK", "application/octet-stream")}
    )
    assert r.status_code == 401
