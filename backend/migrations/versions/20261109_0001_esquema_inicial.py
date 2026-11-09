# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Esquema inicial: mercado laboral (ESCO, O*NET, ofertas, salarios) y gemelo del usuario.

Revisión: 0001
Anterior: ninguna
Fecha: 2026-11-09
"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    op.create_table(
        "competencia",
        sa.Column("uri", sa.String(length=255), nullable=False),
        sa.Column("titulo", sa.String(length=512), nullable=False),
        sa.Column("titulos_alternativos", sa.Text(), nullable=True),
        sa.Column("tipo", sa.String(length=64), nullable=True),
        sa.Column("nivel_reutilizacion", sa.String(length=64), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
        sa.PrimaryKeyConstraint("uri", name=op.f("pk_competencia")),
    )
    op.create_index(op.f("ix_competencia_titulo"), "competencia", ["titulo"], unique=False)
    op.create_table(
        "estadistica_salarial",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fuente", sa.String(length=32), nullable=False),
        sa.Column("codigo_ocupacion", sa.String(length=32), nullable=False),
        sa.Column("periodo", sa.String(length=16), nullable=False),
        sa.Column("medida", sa.String(length=64), nullable=False),
        sa.Column("valor", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_estadistica_salarial")),
        sa.UniqueConstraint(
            "fuente",
            "codigo_ocupacion",
            "periodo",
            "medida",
            name=op.f("uq_estadistica_salarial_fuente"),
        ),
    )
    op.create_index(
        op.f("ix_estadistica_salarial_codigo_ocupacion"),
        "estadistica_salarial",
        ["codigo_ocupacion"],
        unique=False,
    )
    op.create_table(
        "ocupacion",
        sa.Column("uri", sa.String(length=255), nullable=False),
        sa.Column("codigo", sa.String(length=32), nullable=True),
        sa.Column("grupo_isco", sa.String(length=8), nullable=True),
        sa.Column("titulo", sa.String(length=512), nullable=False),
        sa.Column("titulos_alternativos", sa.Text(), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
        sa.PrimaryKeyConstraint("uri", name=op.f("pk_ocupacion")),
    )
    op.create_index(op.f("ix_ocupacion_codigo"), "ocupacion", ["codigo"], unique=False)
    op.create_index(op.f("ix_ocupacion_grupo_isco"), "ocupacion", ["grupo_isco"], unique=False)
    op.create_table(
        "ocupacion_onet",
        sa.Column("codigo", sa.String(length=16), nullable=False),
        sa.Column("titulo", sa.String(length=512), nullable=False),
        sa.PrimaryKeyConstraint("codigo", name=op.f("pk_ocupacion_onet")),
    )
    op.create_table(
        "usuario",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hash_contrasena", sa.String(length=255), nullable=False),
        sa.Column("consentimiento_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consentimiento_version", sa.String(length=16), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuario")),
        sa.UniqueConstraint("email", name=op.f("uq_usuario_email")),
    )
    op.create_table(
        "gemelo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("ocupacion_actual_uri", sa.String(length=255), nullable=True),
        sa.Column("nivel_ingles", sa.String(length=2), nullable=True),
        sa.Column("trayectoria", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ocupacion_actual_uri"],
            ["ocupacion.uri"],
            name=op.f("fk_gemelo_ocupacion_actual_uri_ocupacion"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name=op.f("fk_gemelo_usuario_id_usuario"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gemelo")),
        sa.UniqueConstraint("usuario_id", name=op.f("uq_gemelo_usuario_id")),
    )
    op.create_table(
        "mapeo_esco_onet",
        sa.Column("ocupacion_uri", sa.String(length=255), nullable=False),
        sa.Column("onet_codigo", sa.String(length=16), nullable=False),
        sa.Column("tipo_correspondencia", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(
            ["ocupacion_uri"],
            ["ocupacion.uri"],
            name=op.f("fk_mapeo_esco_onet_ocupacion_uri_ocupacion"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["onet_codigo"],
            ["ocupacion_onet.codigo"],
            name=op.f("fk_mapeo_esco_onet_onet_codigo_ocupacion_onet"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("ocupacion_uri", "onet_codigo", name=op.f("pk_mapeo_esco_onet")),
    )
    op.create_table(
        "ocupacion_competencia",
        sa.Column("ocupacion_uri", sa.String(length=255), nullable=False),
        sa.Column("competencia_uri", sa.String(length=255), nullable=False),
        sa.Column("relacion", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(
            ["competencia_uri"],
            ["competencia.uri"],
            name=op.f("fk_ocupacion_competencia_competencia_uri_competencia"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ocupacion_uri"],
            ["ocupacion.uri"],
            name=op.f("fk_ocupacion_competencia_ocupacion_uri_ocupacion"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "ocupacion_uri", "competencia_uri", name=op.f("pk_ocupacion_competencia")
        ),
    )
    op.create_table(
        "oferta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fuente", sa.String(length=32), nullable=False),
        sa.Column("id_externo", sa.String(length=128), nullable=False),
        sa.Column("titulo", sa.String(length=512), nullable=False),
        sa.Column("empresa", sa.String(length=255), nullable=True),
        sa.Column("provincia", sa.String(length=128), nullable=True),
        sa.Column("ubicacion", sa.String(length=255), nullable=True),
        sa.Column("salario_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("salario_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("texto", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("publicada_en", sa.Date(), nullable=True),
        sa.Column(
            "ingerida_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ocupacion_uri", sa.String(length=255), nullable=True),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
        sa.ForeignKeyConstraint(
            ["ocupacion_uri"],
            ["ocupacion.uri"],
            name=op.f("fk_oferta_ocupacion_uri_ocupacion"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oferta")),
        sa.UniqueConstraint("fuente", "id_externo", name=op.f("uq_oferta_fuente")),
    )
    op.create_index(op.f("ix_oferta_fuente"), "oferta", ["fuente"], unique=False)
    op.create_index(op.f("ix_oferta_ocupacion_uri"), "oferta", ["ocupacion_uri"], unique=False)
    op.create_index(op.f("ix_oferta_provincia"), "oferta", ["provincia"], unique=False)
    op.create_index(op.f("ix_oferta_publicada_en"), "oferta", ["publicada_en"], unique=False)
    op.create_table(
        "transicion_onet",
        sa.Column("origen", sa.String(length=16), nullable=False),
        sa.Column("destino", sa.String(length=16), nullable=False),
        sa.Column("nivel", sa.String(length=32), nullable=False),
        sa.Column("indice", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["destino"],
            ["ocupacion_onet.codigo"],
            name=op.f("fk_transicion_onet_destino_ocupacion_onet"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["origen"],
            ["ocupacion_onet.codigo"],
            name=op.f("fk_transicion_onet_origen_ocupacion_onet"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("origen", "destino", name=op.f("pk_transicion_onet")),
    )
    op.create_table(
        "entrevista",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gemelo_id", sa.Integer(), nullable=False),
        sa.Column("oferta_id", sa.Integer(), nullable=True),
        sa.Column("modo", sa.String(length=8), nullable=False),
        sa.Column("turnos", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("nota_global", sa.Float(), nullable=True),
        sa.Column("nivel_ingles_estimado", sa.String(length=2), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["gemelo_id"],
            ["gemelo.id"],
            name=op.f("fk_entrevista_gemelo_id_gemelo"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["oferta_id"],
            ["oferta.id"],
            name=op.f("fk_entrevista_oferta_id_oferta"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entrevista")),
    )
    op.create_index(op.f("ix_entrevista_gemelo_id"), "entrevista", ["gemelo_id"], unique=False)
    op.create_table(
        "gemelo_competencia",
        sa.Column("gemelo_id", sa.Integer(), nullable=False),
        sa.Column("competencia_uri", sa.String(length=255), nullable=False),
        sa.Column("nivel_declarado", sa.Float(), nullable=True),
        sa.Column("nivel_demostrado", sa.Float(), nullable=True),
        sa.Column("num_evidencias", sa.Integer(), nullable=False),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["competencia_uri"],
            ["competencia.uri"],
            name=op.f("fk_gemelo_competencia_competencia_uri_competencia"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["gemelo_id"],
            ["gemelo.id"],
            name=op.f("fk_gemelo_competencia_gemelo_id_gemelo"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("gemelo_id", "competencia_uri", name=op.f("pk_gemelo_competencia")),
    )
    op.create_table(
        "oferta_competencia",
        sa.Column("oferta_id", sa.Integer(), nullable=False),
        sa.Column("competencia_uri", sa.String(length=255), nullable=False),
        sa.Column("confianza", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["competencia_uri"],
            ["competencia.uri"],
            name=op.f("fk_oferta_competencia_competencia_uri_competencia"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["oferta_id"],
            ["oferta.id"],
            name=op.f("fk_oferta_competencia_oferta_id_oferta"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("oferta_id", "competencia_uri", name=op.f("pk_oferta_competencia")),
    )
    op.create_table(
        "evidencia",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gemelo_id", sa.Integer(), nullable=False),
        sa.Column("competencia_uri", sa.String(length=255), nullable=False),
        sa.Column("origen", sa.String(length=16), nullable=False),
        sa.Column("fragmento", sa.Text(), nullable=True),
        sa.Column("puntuacion", sa.Float(), nullable=True),
        sa.Column("explicacion", sa.Text(), nullable=True),
        sa.Column("entrevista_id", sa.Integer(), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["competencia_uri"],
            ["competencia.uri"],
            name=op.f("fk_evidencia_competencia_uri_competencia"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["entrevista_id"],
            ["entrevista.id"],
            name=op.f("fk_evidencia_entrevista_id_entrevista"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["gemelo_id"],
            ["gemelo.id"],
            name=op.f("fk_evidencia_gemelo_id_gemelo"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidencia")),
    )
    op.create_index(op.f("ix_evidencia_gemelo_id"), "evidencia", ["gemelo_id"], unique=False)

    # Búsqueda aproximada por texto (autocompletado de competencias y ocupaciones)
    op.execute(
        "CREATE INDEX ix_competencia_titulo_trgm ON competencia USING gin (titulo gin_trgm_ops)"
    )
    op.execute("CREATE INDEX ix_ocupacion_titulo_trgm ON ocupacion USING gin (titulo gin_trgm_ops)")
    # Búsqueda semántica por similitud coseno
    for tabla in ("competencia", "ocupacion", "oferta"):
        op.execute(
            f"CREATE INDEX ix_{tabla}_embedding_hnsw ON {tabla} "
            "USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_evidencia_gemelo_id"), table_name="evidencia")
    op.drop_table("evidencia")
    op.drop_table("oferta_competencia")
    op.drop_table("gemelo_competencia")
    op.drop_index(op.f("ix_entrevista_gemelo_id"), table_name="entrevista")
    op.drop_table("entrevista")
    op.drop_table("transicion_onet")
    op.drop_index(op.f("ix_oferta_publicada_en"), table_name="oferta")
    op.drop_index(op.f("ix_oferta_provincia"), table_name="oferta")
    op.drop_index(op.f("ix_oferta_ocupacion_uri"), table_name="oferta")
    op.drop_index(op.f("ix_oferta_fuente"), table_name="oferta")
    op.drop_table("oferta")
    op.drop_table("ocupacion_competencia")
    op.drop_table("mapeo_esco_onet")
    op.drop_table("gemelo")
    op.drop_table("usuario")
    op.drop_table("ocupacion_onet")
    op.drop_index(op.f("ix_ocupacion_grupo_isco"), table_name="ocupacion")
    op.drop_index(op.f("ix_ocupacion_codigo"), table_name="ocupacion")
    op.drop_table("ocupacion")
    op.drop_index(
        op.f("ix_estadistica_salarial_codigo_ocupacion"), table_name="estadistica_salarial"
    )
    op.drop_table("estadistica_salarial")
    op.drop_index(op.f("ix_competencia_titulo"), table_name="competencia")
    op.drop_table("competencia")
