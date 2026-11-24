# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace

from gemelo_core.trayectoria import extraer_perfil


class IAFalsa:
    def __init__(self, respuesta):
        self.respuesta = respuesta
        self.mensajes = []
        self.cfg = SimpleNamespace(llm_modelo_ligero="ligero")

    def completar_json(self, mensajes, **_):
        self.mensajes.append(mensajes)
        return self.respuesta


def test_extrae_la_trayectoria_y_limpia_la_respuesta():
    ia = IAFalsa(
        {
            "resumen": "Administrativa  contable [NOMBRE_1] con 8 años de experiencia.",
            "experiencias": [
                {"puesto": "Auxiliar administrativa", "sector": "Logística", "inicio": 2018},
                {"puesto": "Administrativa contable", "inicio": "2020", "fin": "actualidad"},
                {"puesto": "", "inicio": 2010},
            ],
            "formacion": [{"titulo": "Técnico Superior en Administración", "inicio": 1800}],
            "nivel_ingles": "b2",
        }
    )
    perfil = extraer_perfil(ia, "Currículum seudonimizado")

    assert perfil.resumen == "Administrativa contable con 8 años de experiencia."
    assert [(e.puesto, e.sector, e.inicio, e.fin) for e in perfil.experiencias] == [
        ("Auxiliar administrativa", "Logística", 2018, None),
        ("Administrativa contable", None, 2020, None),
    ]
    assert perfil.formacion[0].inicio is None
    assert perfil.nivel_ingles == "B2"
    assert "Currículum seudonimizado" in ia.mensajes[0][1]["content"]


def test_un_nivel_de_ingles_desconocido_se_descarta():
    perfil = extraer_perfil(IAFalsa({"resumen": None, "nivel_ingles": "nativo"}), "CV")
    assert (perfil.nivel_ingles, perfil.experiencias, perfil.formacion) == (None, [], [])
