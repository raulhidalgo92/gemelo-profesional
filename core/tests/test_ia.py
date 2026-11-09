# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from gemelo_core.ia import convertir_mensajes


def test_convertir_mensajes_separa_sistema_y_traduce_roles():
    sistema, contenidos = convertir_mensajes(
        [
            {"role": "system", "content": "Eres un entrevistador."},
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "¿Qué experiencia tienes?"},
            {"role": "user", "content": "Cinco años con Angular."},
        ]
    )
    assert sistema == "Eres un entrevistador."
    assert [c["role"] for c in contenidos] == ["user", "model", "user"]
    assert contenidos[1]["parts"] == [{"text": "¿Qué experiencia tienes?"}]


def test_sin_mensaje_de_sistema():
    sistema, contenidos = convertir_mensajes([{"role": "user", "content": "Hola"}])
    assert sistema is None
    assert len(contenidos) == 1
