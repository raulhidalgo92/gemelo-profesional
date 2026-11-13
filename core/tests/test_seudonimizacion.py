# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from gemelo_core.seudonimizacion import eliminar_datos_contacto, seudonimizar


def test_sustituye_datos_identificativos():
    texto = (
        "Ana Pérez, ana.perez@correo.es, tlf 612 345 678, DNI 12345678Z, "
        "https://www.linkedin.com/in/ana-perez. Ana Pérez domina Python."
    )
    r = seudonimizar(texto, nombres=["Ana Pérez"])
    assert "ana.perez@correo.es" not in r.texto
    assert "612 345 678" not in r.texto
    assert "12345678Z" not in r.texto
    assert "linkedin.com/in" not in r.texto
    assert "Ana Pérez" not in r.texto
    assert "domina Python" in r.texto
    # El mismo valor recibe siempre el mismo marcador
    assert r.texto.count("[NOMBRE_1]") == 2


def test_es_reversible():
    original = "Contacto: juan@ejemplo.com"
    r = seudonimizar(original)
    assert r.revertir(r.texto) == original


def test_elimina_datos_de_contacto_de_una_oferta():
    texto = (
        "Se busca soldador. Enviar CV a rrhh@empresa.es o llamar al 983 123 456, "
        "preguntar por María López. Persona de contacto: Sr. Gómez."
    )
    limpio = eliminar_datos_contacto(texto)
    for dato in ("rrhh@empresa.es", "983 123 456", "María", "López", "Gómez"):
        assert dato not in limpio
    assert limpio.startswith("Se busca soldador.")
    assert "preguntar por [contacto]" in limpio
