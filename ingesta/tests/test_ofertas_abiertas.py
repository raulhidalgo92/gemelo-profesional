# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from datetime import date

from ingesta.fuentes import ecyl, feina_activa
from ingesta.fuentes._ofertas import limpiar, texto_plano

XML = """<ofertes><feinaactiva>
<ad>
  <id>FA1</id><url>https://feinaactiva.gencat.cat/search/offers/detail/FA1</url>
  <title>AUXILIAR CONTABLE</title><content>Gestión de facturas.</content>
  <company>Empresa Sector Empresarial</company><experience>Experiència 2 anys</experience>
  <requirements/><studies/><contract>Contracte laboral indefinit</contract>
  <workingHours>Jornada completa</workingHours><date>26/08/2026</date>
  <salaryMin>1400</salaryMin><salaryMax>1550</salaryMax>
  <city>SANT CUGAT DEL VALLÈS</city><region>BARCELONA</region>
</ad>
<ad><id>FA2</id><title>DIRECTOR FINANCIERO</title><salaryMin>45000</salaryMin></ad>
<ad><id>FA3</id><title></title></ad>
</feinaactiva></ofertes>"""


def test_feina_activa_normaliza_y_descarta_ofertas_sin_titulo():
    ofertas = list(feina_activa.filas(XML.encode()))
    assert [o["id_externo"] for o in ofertas] == ["FA1", "FA2"]
    o = ofertas[0]
    assert o["provincia"] == "Barcelona" and o["ubicacion"] == "Sant Cugat Del Vallès"
    assert o["publicada_en"] == date(2026, 8, 26)
    assert (o["salario_min"], o["salario_max"], o["salario_periodo"]) == (1400, 1550, "mes")
    assert o["texto"].startswith("Gestión de facturas.")
    assert "Contrato: Contracte laboral indefinit" in o["texto"]
    assert "Requisitos" not in o["texto"]  # las secciones vacías no se añaden
    assert ofertas[1]["salario_periodo"] == "año"


def test_ecyl_convierte_html_a_texto():
    registros = [
        {
            "identificador": 1285692948358,
            "titulo": "Arquitecto/a para Ayto. de Las Navas del Marqu&eacute;s",
            "descripcion": "<p><strong>Plazas:</strong> 1</p><p>Info en el 920 123 456</p>",
            "provincia": "Ávila",
            "localidad_asset0": "Navas del Marqués (Las)",
            "fecha_publicacion": "2026-10-26",
            "enlace_al_contenido": "https://empleo.jcyl.es/oferta/1",
        },
        {"identificador": 2, "titulo": None},
    ]
    ofertas = list(ecyl.filas(registros))
    assert len(ofertas) == 1
    o = limpiar(ofertas[0])
    assert o["id_externo"] == "1285692948358"
    assert o["titulo"] == "Arquitecto/a para Ayto. de Las Navas del Marqués"
    assert o["texto"] == "Plazas: 1 Info en el [contacto]"
    assert o["publicada_en"] == date(2026, 10, 26)


def test_texto_plano_sin_contenido():
    assert texto_plano(None) == ""
