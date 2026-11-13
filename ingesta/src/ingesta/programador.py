# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Programación de la ingesta nocturna de ofertas y cursos."""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from gemelo_core.config import ajustes

log = logging.getLogger(__name__)


def ingesta_nocturna() -> None:
    from ingesta.fuentes import cursos_soc, ecyl, feina_activa

    tareas = (
        ("feina_activa", feina_activa.ingerir),
        ("ecyl", ecyl.ingerir),
        ("cursos_soc", cursos_soc.ingerir),
    )
    for nombre, tarea in tareas:
        try:
            tarea()
        except Exception:  # una fuente caída no debe parar las demás
            log.exception("Fallo en la ingesta de %s", nombre)


def iniciar() -> None:
    cron = ajustes().ingesta_cron
    planificador = BlockingScheduler(timezone="Europe/Madrid")
    planificador.add_job(ingesta_nocturna, CronTrigger.from_crontab(cron), id="ofertas")
    log.info("Programador iniciado. Ingesta de ofertas: '%s'", cron)
    planificador.start()
