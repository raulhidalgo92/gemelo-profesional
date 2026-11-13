# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Catálogo de formación: especialidades e itinerarios del SEPE y cursos programados.

Revisión: 0004
Anterior: 0003
Fecha: 2026-11-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "especialidad_formativa",
        sa.Column("codigo", sa.String(length=32), nullable=False),
        sa.Column("denominacion", sa.String(length=512), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("familia", sa.String(length=128), nullable=True),
        sa.Column("area", sa.String(length=128), nullable=True),
        sa.Column("nivel", sa.Integer(), nullable=True),
        sa.Column("modalidad", sa.String(length=64), nullable=True),
        sa.Column("horas", sa.Integer(), nullable=True),
        sa.Column("horas_presenciales", sa.Integer(), nullable=True),
        sa.Column("competencia_transversal", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("codigo", name=op.f("pk_especialidad_formativa")),
    )
    op.create_index(
        op.f("ix_especialidad_formativa_familia"), "especialidad_formativa", ["familia"]
    )

    op.create_table(
        "especialidad_ocupacion",
        sa.Column("especialidad_codigo", sa.String(length=32), nullable=False),
        sa.Column("codigo_ocupacion", sa.String(length=8), nullable=False),
        sa.Column("cno", sa.String(length=4), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["especialidad_codigo"],
            ["especialidad_formativa.codigo"],
            name=op.f("fk_especialidad_ocupacion_especialidad_codigo_especialidad_formativa"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "especialidad_codigo", "codigo_ocupacion", name=op.f("pk_especialidad_ocupacion")
        ),
    )
    op.create_index(op.f("ix_especialidad_ocupacion_cno"), "especialidad_ocupacion", ["cno"])

    op.create_table(
        "itinerario_formativo",
        sa.Column("codigo", sa.String(length=32), nullable=False),
        sa.Column("denominacion", sa.String(length=512), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("familia", sa.String(length=128), nullable=True),
        sa.Column("nivel", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Integer(), nullable=True),
        sa.Column("competencia_transversal", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("codigo", name=op.f("pk_itinerario_formativo")),
    )

    op.create_table(
        "curso",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fuente", sa.String(length=32), nullable=False),
        sa.Column("id_externo", sa.String(length=128), nullable=False),
        sa.Column("denominacion", sa.String(length=512), nullable=False),
        sa.Column("tipo", sa.String(length=64), nullable=True),
        sa.Column("modalidad", sa.String(length=64), nullable=True),
        sa.Column("horas", sa.Integer(), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("municipio", sa.String(length=128), nullable=True),
        sa.Column("provincia", sa.String(length=128), nullable=True),
        sa.Column("centro", sa.String(length=255), nullable=True),
        sa.Column("estado", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_curso")),
        sa.UniqueConstraint("fuente", "id_externo", name=op.f("uq_curso_fuente")),
    )
    op.create_index(op.f("ix_curso_fuente"), "curso", ["fuente"])
    op.create_index(op.f("ix_curso_fecha_inicio"), "curso", ["fecha_inicio"])
    op.create_index(op.f("ix_curso_provincia"), "curso", ["provincia"])


def downgrade() -> None:
    op.drop_table("curso")
    op.drop_table("itinerario_formativo")
    op.drop_table("especialidad_ocupacion")
    op.drop_table("especialidad_formativa")
