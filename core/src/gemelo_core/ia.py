# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Acceso a modelos de lenguaje y de embeddings.

El resto del código solo conoce la interfaz `ClienteIA`. Hay dos implementaciones:

- `ClienteVertex`: Gemini en Vertex AI con ubicaciones europeas (opción por defecto).
  Se factura con la cuenta de Google Cloud y el procesamiento queda dentro de la UE.
- `ClienteCompatibleOpenAI`: cualquier API con el formato de OpenAI (/chat/completions
  y /embeddings). Permite comparar otros proveedores en la evaluación.

`cliente_ia()` devuelve la implementación indicada en LLM_PROVEEDOR.
"""

import json
import threading
from abc import ABC, abstractmethod
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

from gemelo_core.config import Ajustes, ajustes

# Tipos de tarea de los embeddings: mejoran la calidad si se indica para qué es el texto
TAREA_DOCUMENTO = "RETRIEVAL_DOCUMENT"
TAREA_CONSULTA = "RETRIEVAL_QUERY"


class ErrorIA(RuntimeError):
    pass


class ClienteIA(ABC):
    def __init__(self, cfg: Ajustes | None = None) -> None:
        self.cfg = cfg or ajustes()
        # Tokens consumidos por modelo, para medir el coste real de cada proceso
        self.uso: Counter[str] = Counter()
        self._cerrojo = threading.Lock()

    def contar_tokens(self, modelo: str, entrada: int, salida: int) -> None:
        with self._cerrojo:
            self.uso[f"{modelo}:entrada"] += entrada
            self.uso[f"{modelo}:salida"] += salida

    @abstractmethod
    def completar(
        self,
        mensajes: list[dict[str, str]],
        *,
        modelo: str | None = None,
        temperatura: float = 0.0,
        json_salida: bool = False,
    ) -> str:
        """Genera una respuesta. `mensajes` usa roles system / user / assistant."""

    @abstractmethod
    def embeddings(self, textos: list[str], *, tarea: str | None = None) -> list[list[float]]:
        """Devuelve un vector de `embeddings_dimension` valores por texto."""

    def completar_json(self, mensajes: list[dict[str, str]], **kwargs: Any) -> Any:
        texto = self.completar(mensajes, json_salida=True, **kwargs)
        try:
            return json.loads(texto)
        except json.JSONDecodeError as e:
            raise ErrorIA(f"La respuesta no es JSON válido: {texto[:200]}") from e


class ClienteVertex(ClienteIA):
    """Gemini en Vertex AI mediante el SDK oficial `google-genai`."""

    def __init__(self, cfg: Ajustes | None = None) -> None:
        super().__init__(cfg)
        from google import genai  # importación diferida: solo se necesita con Vertex
        from google.genai import types

        self._types = types
        credenciales = Path(self.cfg.google_application_credentials)
        if not credenciales.exists():
            raise ErrorIA(f"No se encuentra la clave de la cuenta de servicio en {credenciales}")
        proyecto = self.cfg.vertex_proyecto or json.loads(credenciales.read_text())["project_id"]
        cred = _credenciales_servicio(credenciales)

        def cliente(ubicacion: str):
            return genai.Client(
                vertexai=True, project=proyecto, location=ubicacion, credentials=cred
            )

        self._cliente = cliente(self.cfg.vertex_region)
        self._cliente_embeddings = cliente(self.cfg.vertex_region_embeddings)

    def completar(
        self,
        mensajes: list[dict[str, str]],
        *,
        modelo: str | None = None,
        temperatura: float = 0.0,
        json_salida: bool = False,
    ) -> str:
        sistema, contenidos = convertir_mensajes(mensajes)
        config = self._types.GenerateContentConfig(
            system_instruction=sistema,
            temperature=temperatura,
            response_mime_type="application/json" if json_salida else None,
        )
        modelo = modelo or self.cfg.llm_modelo
        try:
            r = self._cliente.models.generate_content(
                model=modelo, contents=contenidos, config=config
            )
        except Exception as e:
            raise ErrorIA(f"Vertex AI: {e}") from e
        if r.usage_metadata:
            self.contar_tokens(
                modelo,
                r.usage_metadata.prompt_token_count or 0,
                r.usage_metadata.candidates_token_count or 0,
            )
        return r.text or ""

    def embeddings(self, textos: list[str], *, tarea: str | None = None) -> list[list[float]]:
        config = self._types.EmbedContentConfig(
            output_dimensionality=self.cfg.embeddings_dimension, task_type=tarea
        )
        try:
            r = self._cliente_embeddings.models.embed_content(
                model=self.cfg.embeddings_modelo, contents=textos, config=config
            )
        except Exception as e:
            raise ErrorIA(f"Vertex AI (embeddings): {e}") from e
        return [e.values for e in r.embeddings]


class ClienteCompatibleOpenAI(ClienteIA):
    """Cualquier proveedor que implemente /chat/completions y /embeddings."""

    def __init__(self, cfg: Ajustes | None = None, timeout: float = 60.0) -> None:
        super().__init__(cfg)
        self._http = httpx.Client(
            base_url=self.cfg.llm_base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {self.cfg.llm_api_key}"},
            timeout=timeout,
        )

    def completar(
        self,
        mensajes: list[dict[str, str]],
        *,
        modelo: str | None = None,
        temperatura: float = 0.0,
        json_salida: bool = False,
    ) -> str:
        cuerpo: dict[str, Any] = {
            "model": modelo or self.cfg.llm_modelo,
            "messages": mensajes,
            "temperature": temperatura,
        }
        if json_salida:
            cuerpo["response_format"] = {"type": "json_object"}
        r = self._http.post("/chat/completions", json=cuerpo)
        if r.status_code >= 400:
            raise ErrorIA(f"LLM {r.status_code}: {r.text[:300]}")
        datos = r.json()
        uso = datos.get("usage") or {}
        self.contar_tokens(
            cuerpo["model"], uso.get("prompt_tokens", 0), uso.get("completion_tokens", 0)
        )
        return datos["choices"][0]["message"]["content"]

    def embeddings(self, textos: list[str], *, tarea: str | None = None) -> list[list[float]]:
        r = self._http.post(
            "/embeddings",
            json={
                "model": self.cfg.embeddings_modelo,
                "input": textos,
                "dimensions": self.cfg.embeddings_dimension,
            },
        )
        if r.status_code >= 400:
            raise ErrorIA(f"Embeddings {r.status_code}: {r.text[:300]}")
        datos = sorted(r.json()["data"], key=lambda d: d["index"])
        return [d["embedding"] for d in datos]


def convertir_mensajes(mensajes: list[dict[str, str]]) -> tuple[str | None, list[dict]]:
    """Pasa mensajes estilo OpenAI al formato de Gemini (instrucción de sistema aparte)."""
    sistema = "\n\n".join(m["content"] for m in mensajes if m["role"] == "system") or None
    contenidos = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
        for m in mensajes
        if m["role"] != "system"
    ]
    return sistema, contenidos


def _credenciales_servicio(ruta: Path):
    from google.oauth2 import service_account

    return service_account.Credentials.from_service_account_file(
        str(ruta), scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )


@lru_cache
def cliente_ia() -> ClienteIA:
    proveedor = ajustes().llm_proveedor
    if proveedor == "vertex":
        return ClienteVertex()
    if proveedor == "openai":
        return ClienteCompatibleOpenAI()
    raise ErrorIA(f"LLM_PROVEEDOR desconocido: {proveedor}")
