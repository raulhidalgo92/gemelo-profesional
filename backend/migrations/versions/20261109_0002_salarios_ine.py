# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Salarios del INE: correspondencia CNO-11 ↔ ISCO-08 y columnas descriptivas.

Revisión: 0002
Anterior: 0001
Fecha: 2026-11-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "correspondencia_cno_isco",
        sa.Column("cno", sa.String(length=4), nullable=False),
        sa.Column("isco", sa.String(length=4), nullable=False),
        sa.Column("titulo_cno", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("cno", "isco", name=op.f("pk_correspondencia_cno_isco")),
    )
    op.create_index(op.f("ix_correspondencia_cno_isco_isco"), "correspondencia_cno_isco", ["isco"])
    op.add_column(
        "estadistica_salarial", sa.Column("descripcion", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "estadistica_salarial",
        sa.Column("precision_baja", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("estadistica_salarial", "precision_baja")
    op.drop_column("estadistica_salarial", "descripcion")
    op.drop_index(op.f("ix_correspondencia_cno_isco_isco"), table_name="correspondencia_cno_isco")
    op.drop_table("correspondencia_cno_isco")
