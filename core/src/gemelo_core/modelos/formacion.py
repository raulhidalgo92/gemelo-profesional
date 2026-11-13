# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Dominio «formación»: catálogo oficial de especialidades del SEPE y cursos programados.

Las especialidades se enlazan con ESCO a través de sus ocupaciones relacionadas
(CNO-11 → ISCO-08 con la correspondencia del INE → ocupaciones ESCO).
"""

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gemelo_core.modelos.base import Base


class EspecialidadFormativa(Base):
    """Especialidad del Catálogo de Especialidades Formativas del SEPE (Orden TMS/283/2019)."""

    __tablename__ = "especialidad_formativa"

    codigo: Mapped[str] = mapped_column(String(32), primary_key=True)
    denominacion: Mapped[str] = mapped_column(String(512))
    version: Mapped[int] = mapped_column(Integer, default=1)
    familia: Mapped[str | None] = mapped_column(String(128), index=True)
    area: Mapped[str | None] = mapped_column(String(128))
    nivel: Mapped[int | None] = mapped_column(Integer)  # nivel de cualificación 1-5
    modalidad: Mapped[str | None] = mapped_column(String(64))
    horas: Mapped[int | None] = mapped_column(Integer)
    horas_presenciales: Mapped[int | None] = mapped_column(Integer)
    competencia_transversal: Mapped[str | None] = mapped_column(String(128))

    ocupaciones: Mapped[list["EspecialidadOcupacion"]] = relationship(
        back_populates="especialidad", cascade="all, delete-orphan"
    )


class EspecialidadOcupacion(Base):
    """Ocupación relacionada con una especialidad, con su código del SEPE de 8 dígitos."""

    __tablename__ = "especialidad_ocupacion"

    especialidad_codigo: Mapped[str] = mapped_column(
        ForeignKey("especialidad_formativa.codigo", ondelete="CASCADE"), primary_key=True
    )
    codigo_ocupacion: Mapped[str] = mapped_column(String(8), primary_key=True)
    cno: Mapped[str] = mapped_column(String(4), index=True)  # los 4 primeros dígitos (CNO-11)
    titulo: Mapped[str] = mapped_column(String(255))

    especialidad: Mapped[EspecialidadFormativa] = relationship(back_populates="ocupaciones")


class ItinerarioFormativo(Base):
    """Itinerario del catálogo del SEPE: un conjunto de especialidades que forman una ruta."""

    __tablename__ = "itinerario_formativo"

    codigo: Mapped[str] = mapped_column(String(32), primary_key=True)
    denominacion: Mapped[str] = mapped_column(String(512))
    version: Mapped[int] = mapped_column(Integer, default=1)
    familia: Mapped[str | None] = mapped_column(String(128))
    nivel: Mapped[int | None] = mapped_column(Integer)
    horas: Mapped[int | None] = mapped_column(Integer)
    competencia_transversal: Mapped[str | None] = mapped_column(String(128))


class Curso(Base):
    """Curso programado por un servicio público de empleo (fecha, lugar y modalidad)."""

    __tablename__ = "curso"
    __table_args__ = (UniqueConstraint("fuente", "id_externo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fuente: Mapped[str] = mapped_column(String(32), index=True)  # cursos_soc
    id_externo: Mapped[str] = mapped_column(String(128))
    denominacion: Mapped[str] = mapped_column(String(512))
    tipo: Mapped[str | None] = mapped_column(String(64))
    modalidad: Mapped[str | None] = mapped_column(String(64))
    horas: Mapped[int | None] = mapped_column(Integer)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, index=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    municipio: Mapped[str | None] = mapped_column(String(128))
    provincia: Mapped[str | None] = mapped_column(String(128), index=True)
    centro: Mapped[str | None] = mapped_column(String(255))
    estado: Mapped[str | None] = mapped_column(String(128))
