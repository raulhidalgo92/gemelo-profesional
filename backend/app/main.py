# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Punto de entrada de la API REST."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from gemelo_core import __version__
from gemelo_core.config import ajustes

app = FastAPI(
    title="Gemelo digital profesional",
    version=__version__,
    description=(
        "API del gemelo digital profesional. Trabajo de Fin de Grado, "
        "Grado en Ingeniería Informática, UNIR."
    ),
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ajustes().lista_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
