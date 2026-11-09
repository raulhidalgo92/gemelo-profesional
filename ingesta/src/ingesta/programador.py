# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Programación de la ingesta nocturna de ofertas."""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from gemelo_core.config import ajustes

log = logging.getLogger(__name__)


def ingesta_nocturna() -> None:
    from ingesta.fuentes import eures, infojobs

    for nombre, tarea in (("infojobs", infojobs.ingerir), ("eures", eures.ingerir)):
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
