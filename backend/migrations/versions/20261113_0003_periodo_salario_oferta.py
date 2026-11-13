# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Periodo del salario de las ofertas (mensual o anual).

Revisión: 0003
Anterior: 0002
Fecha: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("oferta", sa.Column("salario_periodo", sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column("oferta", "salario_periodo")
