# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Dominio «usuario»: cuenta, gemelo profesional, evidencias y entrevistas.

El gemelo distingue entre competencias DECLARADAS (CV/LinkedIn) y
DEMOSTRADAS (entrevistas, tests). Cada evidencia ajusta el nivel de la
competencia y dispara el recálculo de trayectorias y encajes.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gemelo_core.modelos.base import Base, ConMarcasTiempo


class Usuario(ConMarcasTiempo, Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    hash_contrasena: Mapped[str] = mapped_column(String(255))
    # RGPD: fecha y versión del texto de consentimiento aceptado
    consentimiento_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consentimiento_version: Mapped[str | None] = mapped_column(String(16))

    gemelo: Mapped["Gemelo"] = relationship(
        back_populates="usuario", cascade="all, delete-orphan", uselist=False
    )


class Gemelo(ConMarcasTiempo, Base):
    """Gemelo digital profesional de un usuario."""

    __tablename__ = "gemelo"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), unique=True
    )
    ocupacion_actual_uri: Mapped[str | None] = mapped_column(
        ForeignKey("ocupacion.uri", ondelete="SET NULL")
    )
    nivel_ingles: Mapped[str | None] = mapped_column(String(2))  # MCER: A1..C2
    # Resumen seudonimizado de la trayectoria (sin datos identificativos)
    trayectoria: Mapped[dict | None] = mapped_column(JSONB)

    usuario: Mapped[Usuario] = relationship(back_populates="gemelo")
    competencias: Mapped[list["GemeloCompetencia"]] = relationship(
        back_populates="gemelo", cascade="all, delete-orphan"
    )


class GemeloCompetencia(Base):
    """Estado de una competencia ESCO dentro del gemelo."""

    __tablename__ = "gemelo_competencia"

    gemelo_id: Mapped[int] = mapped_column(
        ForeignKey("gemelo.id", ondelete="CASCADE"), primary_key=True
    )
    competencia_uri: Mapped[str] = mapped_column(
        ForeignKey("competencia.uri", ondelete="CASCADE"), primary_key=True
    )
    nivel_declarado: Mapped[float | None] = mapped_column(Float)  # 0..1
    nivel_demostrado: Mapped[float | None] = mapped_column(Float)  # 0..1
    num_evidencias: Mapped[int] = mapped_column(Integer, default=0)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    gemelo: Mapped[Gemelo] = relationship(back_populates="competencias")


class Evidencia(Base):
    """Prueba que respalda (o no) una competencia: fragmento de CV, respuesta de entrevista..."""

    __tablename__ = "evidencia"

    id: Mapped[int] = mapped_column(primary_key=True)
    gemelo_id: Mapped[int] = mapped_column(ForeignKey("gemelo.id", ondelete="CASCADE"), index=True)
    competencia_uri: Mapped[str] = mapped_column(ForeignKey("competencia.uri", ondelete="CASCADE"))
    origen: Mapped[str] = mapped_column(String(16))  # cv | linkedin | entrevista | test
    fragmento: Mapped[str | None] = mapped_column(Text)
    puntuacion: Mapped[float | None] = mapped_column(Float)  # 0..1
    explicacion: Mapped[str | None] = mapped_column(Text)
    entrevista_id: Mapped[int | None] = mapped_column(
        ForeignKey("entrevista.id", ondelete="CASCADE")
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Entrevista(Base):
    """Sesión de entrevista simulada. Solo se guarda texto: el audio se descarta."""

    __tablename__ = "entrevista"

    id: Mapped[int] = mapped_column(primary_key=True)
    gemelo_id: Mapped[int] = mapped_column(ForeignKey("gemelo.id", ondelete="CASCADE"), index=True)
    oferta_id: Mapped[int | None] = mapped_column(ForeignKey("oferta.id", ondelete="SET NULL"))
    modo: Mapped[str] = mapped_column(String(8), default="texto")  # texto | voz
    turnos: Mapped[list | None] = mapped_column(JSONB)  # [{rol, texto, ...}]
    nota_global: Mapped[float | None] = mapped_column(Float)
    nivel_ingles_estimado: Mapped[str | None] = mapped_column(String(2))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
