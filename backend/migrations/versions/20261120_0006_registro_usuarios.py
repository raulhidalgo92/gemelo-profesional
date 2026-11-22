# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Registro de usuarios: verificación del correo, sesiones y asistente de bienvenida.

Revisión: 0006
Anterior: 0005
Fecha: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "usuario", sa.Column("nombre", sa.String(length=80), nullable=False, server_default="")
    )
    op.add_column("usuario", sa.Column("verificado_en", sa.DateTime(timezone=True)))
    op.add_column("usuario", sa.Column("bienvenida_en", sa.DateTime(timezone=True)))

    op.create_table(
        "codigo_verificacion",
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("hash_codigo", sa.String(length=64), nullable=False),
        sa.Column("hash_enlace", sa.String(length=64), nullable=False),
        sa.Column("intentos", sa.SmallInteger(), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("enviado_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_codigo_verificacion_usuario_id_usuario"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("usuario_id", name=op.f("pk_codigo_verificacion")),
        sa.UniqueConstraint("hash_enlace", name=op.f("uq_codigo_verificacion_hash_enlace")),
    )
    op.create_table(
        "sesion_usuario",
        sa.Column("hash_token", sa.String(length=64), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column(
            "creada_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_sesion_usuario_usuario_id_usuario"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("hash_token", name=op.f("pk_sesion_usuario")),
    )
    op.create_index(op.f("ix_sesion_usuario_usuario_id"), "sesion_usuario", ["usuario_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_sesion_usuario_usuario_id"), table_name="sesion_usuario")
    op.drop_table("sesion_usuario")
    op.drop_table("codigo_verificacion")
    op.drop_column("usuario", "bienvenida_en")
    op.drop_column("usuario", "verificado_en")
    op.drop_column("usuario", "nombre")
