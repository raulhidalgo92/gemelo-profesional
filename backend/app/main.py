# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Punto de entrada de la API REST."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}
CABECERA_CSRF = "X-Requested-With"


@app.middleware("http")
async def proteger_csrf(request: Request, siguiente):
    """La sesión va en una cookie, así que las peticiones que modifican datos deben llevar
    una cabecera propia: un formulario de otra web no puede añadirla."""
    if request.method not in METODOS_SEGUROS and CABECERA_CSRF.lower() not in request.headers:
        return JSONResponse({"detail": "falta_cabecera_csrf"}, status_code=403)
    return await siguiente(request)


app.include_router(router, prefix="/api")
