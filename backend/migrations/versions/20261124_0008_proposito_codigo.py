# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Propósito de los códigos enviados por correo: activación o recuperación de la contraseña.

Revisión: 0008
Anterior: 0007
Fecha: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "codigo_verificacion",
        sa.Column("proposito", sa.String(length=12), nullable=False, server_default="activacion"),
    )


def downgrade() -> None:
    op.drop_column("codigo_verificacion", "proposito")
