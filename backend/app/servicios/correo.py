# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Envío de correos con plantillas HTML y texto plano.

En desarrollo los recoge Mailpit; en producción, el SMTP de un proveedor de la UE.
Nunca se registra en los logs el destinatario ni el contenido.
"""

import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from gemelo_core.config import ajustes

log = logging.getLogger(__name__)

_plantillas = Environment(
    loader=FileSystemLoader(Path(__file__).parent.parent / "plantillas" / "correo"),
    autoescape=select_autoescape(["html"]),
)


def componer(destino: str, asunto: str, plantilla: str, **datos) -> EmailMessage:
    cfg = ajustes()
    datos = {"url_publica": cfg.url_publica, **datos}
    msg = EmailMessage()
    msg["From"] = cfg.correo_remitente
    msg["To"] = destino
    msg["Subject"] = asunto
    msg.set_content(_plantillas.get_template(f"{plantilla}.txt").render(**datos))
    msg.add_alternative(_plantillas.get_template(f"{plantilla}.html").render(**datos), "html")
    return msg


def enviar(msg: EmailMessage) -> None:
    cfg = ajustes()
    try:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_puerto, timeout=15) as smtp:
            if cfg.smtp_starttls:
                smtp.starttls()
            if cfg.smtp_usuario:
                smtp.login(cfg.smtp_usuario, cfg.smtp_contrasena)
            smtp.send_message(msg)
    except (OSError, smtplib.SMTPException) as e:
        log.error("No se ha podido enviar un correo («%s»): %s", msg["Subject"], type(e).__name__)
