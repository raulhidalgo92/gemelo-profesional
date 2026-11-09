# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Configuración leída de variables de entorno (ver .env.example)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Ajustes(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://gemelo:gemelo@localhost:5432/gemelo"
    secret_key: str = "solo-para-desarrollo"
    cors_origins: str = "http://localhost:4200"

    # Proveedor de modelos de lenguaje: "vertex" (Gemini en Vertex AI, región UE)
    # o "openai" (cualquier API compatible con el formato de OpenAI)
    llm_proveedor: str = "vertex"
    llm_modelo: str = "gemini-3.8-flash"
    llm_modelo_ligero: str = "gemini-3.1-flash-lite"
    embeddings_modelo: str = "gemini-embedding-001"
    embeddings_dimension: int = 1024

    # Vertex AI: proyecto (si se deja vacío se toma del JSON de la cuenta de servicio) y
    # ubicaciones europeas. Los modelos Gemini se sirven en la multirregión «eu» y los de
    # embeddings en regiones concretas, así que se configuran por separado.
    vertex_proyecto: str = ""
    vertex_region: str = "eu"
    vertex_region_embeddings: str = "europe-west1"
    google_application_credentials: str = "/run/secretos/vertex.json"

    # Proveedor alternativo compatible con OpenAI
    llm_base_url: str = ""
    llm_api_key: str = ""

    infojobs_client_id: str = ""
    infojobs_client_secret: str = ""
    esco_api_url: str = "https://ec.europa.eu/esco/api"
    onet_url: str = "https://www.onetcenter.org/dl_files/database/db_31_0_text.zip"
    esco_onet_url: str = (
        "https://esco.ec.europa.eu/system/files/2023-08/ONET_%28Occupations%29_0_updated.csv"
    )

    ingesta_cron: str = "0 3 * * *"
    directorio_datos: str = "/data"

    @property
    def lista_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def ajustes() -> Ajustes:
    return Ajustes()
