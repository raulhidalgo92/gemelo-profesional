# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from ingesta.fuentes import esco_api

BASE = "http://data.europa.eu/esco"

OCUPACION = {
    "uri": f"{BASE}/occupation/o1",
    "code": "2512.3",
    "preferredLabel": {"es": "desarrollador de software", "en": "software developer"},
    "alternativeLabel": {"es": ["programador", "desarrolladora de aplicaciones"]},
    "description": {"es": {"literal": "Implementan programas.", "mimetype": "plain/text"}},
    "_links": {
        "broaderIscoGroup": [{"uri": f"{BASE}/isco/C2512", "code": "2512"}],
        "hasEssentialSkill": [{"uri": f"{BASE}/skill/s1"}],
        "hasOptionalSkill": [{"uri": f"{BASE}/skill/s2"}],
    },
}

COMPETENCIA = {
    "uri": f"{BASE}/skill/s1",
    "title": "define technical requirements",
    "preferredLabel": {"es": "definir requisitos técnicos"},
    "description": {"es": {"literal": " Especificar propiedades. "}},
    "_links": {
        "hasSkillType": [{"uri": f"{BASE}/skill-type/skill"}],
        "hasReuseLevel": [{"uri": f"{BASE}/skill-reuse-level/cross-sector"}],
    },
}


def test_normaliza_ocupacion():
    f = esco_api.normalizar_ocupacion(OCUPACION)
    assert f["titulo"] == "desarrollador de software"
    assert f["codigo"] == "2512.3"
    assert f["grupo_isco"] == "2512"
    assert f["titulos_alternativos"] == "programador\ndesarrolladora de aplicaciones"
    assert f["descripcion"] == "Implementan programas."


def test_normaliza_competencia():
    f = esco_api.normalizar_competencia(COMPETENCIA)
    assert f["titulo"] == "definir requisitos técnicos"
    assert f["tipo"] == "skill"
    assert f["nivel_reutilizacion"] == "cross-sector"
    assert f["descripcion"] == "Especificar propiedades."
    assert f["titulos_alternativos"] is None


def test_competencia_sin_espanol_usa_titulo():
    f = esco_api.normalizar_competencia({"uri": "x", "title": "fallback", "_links": {}})
    assert f["titulo"] == "fallback"
    assert f["tipo"] is None


def test_relaciones():
    rel = list(esco_api.relaciones_de(OCUPACION))
    assert {(r["competencia_uri"].rsplit("/", 1)[-1], r["relacion"]) for r in rel} == {
        ("s1", "essential"),
        ("s2", "optional"),
    }


class _HttpFalso:
    """Simula /search de ESCO, donde `offset` es el número de página."""

    def __init__(self, total: int):
        self.uris = [f"u{i}" for i in range(total)]
        self.paginas_pedidas: list[int] = []

    def get(self, ruta, params):
        pagina, limite = params["offset"], params["limit"]
        self.paginas_pedidas.append(pagina)
        trozo = self.uris[pagina * limite : (pagina + 1) * limite]

        class R:
            def raise_for_status(self):
                pass

            def json(_):
                resultados = [{"uri": u} for u in trozo]
                return {"total": len(self.uris), "_embedded": {"results": resultados}}

        return R()


def test_listar_uris_pagina_por_numero_de_pagina(monkeypatch):
    monkeypatch.setattr(esco_api, "TAM_PAGINA", 10)
    monkeypatch.setattr(esco_api, "PAUSA_SEGUNDOS", 0)
    http = _HttpFalso(total=25)
    uris = esco_api.listar_uris(http, "skill")
    assert len(uris) == 25
    assert http.paginas_pedidas == [0, 1, 2]


def test_lote_que_falla_se_parte_y_omite_solo_la_uri_mala(monkeypatch):
    import httpx

    def get_falso(http, ruta, params):
        uris = [v for k, v in params if k == "uris"]
        if "mala" in uris:
            raise httpx.TransportError("500")
        return {"_embedded": {u: {"uri": u} for u in uris}}

    monkeypatch.setattr(esco_api, "_get", get_falso)
    fallidas: list[str] = []
    res = esco_api._detalle_lote(None, "skill", ["a", "b", "mala", "c"], fallidas)
    assert sorted(r["uri"] for r in res) == ["a", "b", "c"]
    assert fallidas == ["mala"]
