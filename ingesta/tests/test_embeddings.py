# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from gemelo_core.ia import ClienteIA, ErrorIA
from ingesta.fuentes import embeddings


class ClienteFalso(ClienteIA):
    """Solo acepta un texto por llamada, como algunos modelos de embeddings."""

    def __init__(self):
        self.llamadas = 0

    def completar(self, mensajes, **kwargs):
        raise NotImplementedError

    def embeddings(self, textos, *, tarea=None):
        self.llamadas += 1
        if len(textos) > 1:
            raise ErrorIA("solo se admite un texto por petición")
        return [[float(len(textos[0]))]]


def test_texto_concepto_combina_titulo_sinonimos_y_descripcion():
    texto = embeddings.texto_concepto("Angular", "AngularJS\n\nAngular 2", "Marco de trabajo.")
    assert texto == "Angular\nTambién: AngularJS, Angular 2.\nMarco de trabajo."


def test_texto_concepto_sin_extras():
    assert embeddings.texto_concepto(" SQL ", None, None) == "SQL"


def test_vectorizar_pasa_a_uno_en_uno_si_no_admite_lotes(monkeypatch):
    monkeypatch.setattr(embeddings.time, "sleep", lambda _: None)
    cliente = ClienteFalso()
    vectores = embeddings.vectorizar(cliente, ["a", "bb", "ccc"])
    assert vectores == [[1.0], [2.0], [3.0]]
