# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Cliente mínimo para APIs de modelos de lenguaje compatibles con OpenAI.

Se usa el formato /chat/completions y /embeddings porque lo implementan casi
todos los proveedores (Mistral, Scaleway, OpenAI, Ollama...). Así el proveedor
se cambia solo con variables de entorno y se puede comparar en la evaluación.
"""

import json
from typing import Any

import httpx

from gemelo_core.config import Ajustes, ajustes


class ErrorIA(RuntimeError):
    pass


class ClienteIA:
    def __init__(self, cfg: Ajustes | None = None, timeout: float = 60.0) -> None:
        self.cfg = cfg or ajustes()
        self._http = httpx.Client(
            base_url=self.cfg.llm_base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {self.cfg.llm_api_key}"},
            timeout=timeout,
        )

    def completar(
        self,
        mensajes: list[dict[str, str]],
        *,
        temperatura: float = 0.0,
        json_salida: bool = False,
    ) -> str:
        cuerpo: dict[str, Any] = {
            "model": self.cfg.llm_modelo,
            "messages": mensajes,
            "temperature": temperatura,
        }
        if json_salida:
            cuerpo["response_format"] = {"type": "json_object"}
        r = self._http.post("/chat/completions", json=cuerpo)
        if r.status_code >= 400:
            raise ErrorIA(f"LLM {r.status_code}: {r.text[:300]}")
        return r.json()["choices"][0]["message"]["content"]

    def completar_json(self, mensajes: list[dict[str, str]]) -> Any:
        texto = self.completar(mensajes, json_salida=True)
        try:
            return json.loads(texto)
        except json.JSONDecodeError as e:
            raise ErrorIA(f"Respuesta no es JSON válido: {texto[:200]}") from e

    def embeddings(self, textos: list[str]) -> list[list[float]]:
        r = self._http.post(
            "/embeddings", json={"model": self.cfg.embeddings_modelo, "input": textos}
        )
        if r.status_code >= 400:
            raise ErrorIA(f"Embeddings {r.status_code}: {r.text[:300]}")
        datos = sorted(r.json()["data"], key=lambda d: d["index"])
        return [d["embedding"] for d in datos]
