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

    llm_base_url: str = "https://api.mistral.ai/v1"
    llm_api_key: str = ""
    llm_modelo: str = "mistral-small-latest"
    embeddings_modelo: str = "mistral-embed"
    embeddings_dimension: int = 1024

    infojobs_client_id: str = ""
    infojobs_client_secret: str = ""
    esco_api_url: str = "https://ec.europa.eu/esco/api"

    ingesta_cron: str = "0 3 * * *"
    directorio_datos: str = "/data"

    @property
    def lista_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def ajustes() -> Ajustes:
    return Ajustes()
