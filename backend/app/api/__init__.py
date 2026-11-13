# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter

from app.api import competencias, formacion, mercado, salud

router = APIRouter()
router.include_router(salud.router, tags=["salud"])
router.include_router(competencias.router, prefix="/competencias", tags=["competencias"])
router.include_router(mercado.router, prefix="/mercado", tags=["mercado"])
router.include_router(formacion.router, prefix="/formacion", tags=["formación"])
