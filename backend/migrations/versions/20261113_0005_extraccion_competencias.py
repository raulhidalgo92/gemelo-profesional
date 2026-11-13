# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Extracción de competencias de ofertas: fecha de proceso y término original.

Revisión: 0005
Anterior: 0004
Fecha: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("oferta", sa.Column("procesada_en", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_oferta_procesada_en"), "oferta", ["procesada_en"])
    op.add_column("oferta_competencia", sa.Column("termino", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("oferta_competencia", "termino")
    op.drop_index(op.f("ix_oferta_procesada_en"), table_name="oferta")
    op.drop_column("oferta", "procesada_en")
