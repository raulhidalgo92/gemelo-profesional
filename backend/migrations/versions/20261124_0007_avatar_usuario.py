# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Avatar elegido por el usuario (de una colección propia; nunca una foto).

Revisión: 0007
Anterior: 0006
Fecha: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("avatar", sa.String(length=16)))


def downgrade() -> None:
    op.drop_column("usuario", "avatar")
