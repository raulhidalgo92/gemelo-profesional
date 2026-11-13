# Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
# SPDX-License-Identifier: Apache-2.0
"""Dominio «mercado»: vocabulario ESCO, transiciones O*NET, ofertas y salarios.

ESCO es el idioma común: toda oferta, currículum o entrevista acaba expresada
como un conjunto de competencias ESCO identificadas por su URI.
"""

from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gemelo_core.modelos.base import Base

# Dimensión de los vectores de embeddings (gemini-embedding-001 reducido a 1024).
DIMENSION_EMBEDDING = 1024


class Ocupacion(Base):
    """Ocupación ESCO (p. ej. «desarrollador de software»)."""

    __tablename__ = "ocupacion"

    uri: Mapped[str] = mapped_column(String(255), primary_key=True)
    codigo: Mapped[str | None] = mapped_column(String(32), index=True)
    grupo_isco: Mapped[str | None] = mapped_column(String(8), index=True)
    titulo: Mapped[str] = mapped_column(String(512))
    titulos_alternativos: Mapped[str | None] = mapped_column(Text)
    descripcion: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(DIMENSION_EMBEDDING))

    competencias: Mapped[list["OcupacionCompetencia"]] = relationship(
        back_populates="ocupacion", cascade="all, delete-orphan"
    )


class Competencia(Base):
    """Competencia o conocimiento ESCO."""

    __tablename__ = "competencia"

    uri: Mapped[str] = mapped_column(String(255), primary_key=True)
    titulo: Mapped[str] = mapped_column(String(512), index=True)
    titulos_alternativos: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str | None] = mapped_column(String(64))  # skill | knowledge
    nivel_reutilizacion: Mapped[str | None] = mapped_column(String(64))
    descripcion: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(DIMENSION_EMBEDDING))


class OcupacionCompetencia(Base):
    """Relación ocupación-competencia de ESCO (esencial u opcional)."""

    __tablename__ = "ocupacion_competencia"

    ocupacion_uri: Mapped[str] = mapped_column(
        ForeignKey("ocupacion.uri", ondelete="CASCADE"), primary_key=True
    )
    competencia_uri: Mapped[str] = mapped_column(
        ForeignKey("competencia.uri", ondelete="CASCADE"), primary_key=True
    )
    relacion: Mapped[str] = mapped_column(String(16))  # essential | optional

    ocupacion: Mapped[Ocupacion] = relationship(back_populates="competencias")
    competencia: Mapped[Competencia] = relationship()


class OcupacionOnet(Base):
    """Ocupación O*NET-SOC (se usa para la matriz de ocupaciones relacionadas)."""

    __tablename__ = "ocupacion_onet"

    codigo: Mapped[str] = mapped_column(String(16), primary_key=True)
    titulo: Mapped[str] = mapped_column(String(512))


class TransicionOnet(Base):
    """Fila de la matriz «Related Occupations» de O*NET: base del Sankey."""

    __tablename__ = "transicion_onet"

    origen: Mapped[str] = mapped_column(
        ForeignKey("ocupacion_onet.codigo", ondelete="CASCADE"), primary_key=True
    )
    destino: Mapped[str] = mapped_column(
        ForeignKey("ocupacion_onet.codigo", ondelete="CASCADE"), primary_key=True
    )
    nivel: Mapped[str] = mapped_column(String(32))  # Primary-Short, Primary-Long, Supplemental
    indice: Mapped[int] = mapped_column(Integer)


class MapeoEscoOnet(Base):
    """Tabla de correspondencias oficial ESCO ↔ O*NET."""

    __tablename__ = "mapeo_esco_onet"

    ocupacion_uri: Mapped[str] = mapped_column(
        ForeignKey("ocupacion.uri", ondelete="CASCADE"), primary_key=True
    )
    onet_codigo: Mapped[str] = mapped_column(
        ForeignKey("ocupacion_onet.codigo", ondelete="CASCADE"), primary_key=True
    )
    tipo_correspondencia: Mapped[str | None] = mapped_column(String(32))


class Oferta(Base):
    """Oferta de empleo normalizada, venga de un servicio público de empleo o del usuario."""

    __tablename__ = "oferta"
    __table_args__ = (UniqueConstraint("fuente", "id_externo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fuente: Mapped[str] = mapped_column(String(32), index=True)  # feina_activa | ecyl | usuario
    id_externo: Mapped[str] = mapped_column(String(128))
    titulo: Mapped[str] = mapped_column(String(512))
    empresa: Mapped[str | None] = mapped_column(String(255))
    provincia: Mapped[str | None] = mapped_column(String(128), index=True)
    ubicacion: Mapped[str | None] = mapped_column(String(255))
    salario_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    salario_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    salario_periodo: Mapped[str | None] = mapped_column(String(8))  # mes | año
    texto: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1024))
    publicada_en: Mapped[date | None] = mapped_column(Date, index=True)
    ingerida_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ocupacion_uri: Mapped[str | None] = mapped_column(
        ForeignKey("ocupacion.uri", ondelete="SET NULL"), index=True
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(DIMENSION_EMBEDDING))

    competencias: Mapped[list["OfertaCompetencia"]] = relationship(
        back_populates="oferta", cascade="all, delete-orphan"
    )


class OfertaCompetencia(Base):
    """Competencia ESCO detectada en una oferta, con la confianza del extractor."""

    __tablename__ = "oferta_competencia"

    oferta_id: Mapped[int] = mapped_column(
        ForeignKey("oferta.id", ondelete="CASCADE"), primary_key=True
    )
    competencia_uri: Mapped[str] = mapped_column(
        ForeignKey("competencia.uri", ondelete="CASCADE"), primary_key=True
    )
    confianza: Mapped[float] = mapped_column(Float, default=1.0)

    oferta: Mapped[Oferta] = relationship(back_populates="competencias")


class EstadisticaSalarial(Base):
    """Dato salarial agregado (INE, Cedefop...) por ocupación y periodo."""

    __tablename__ = "estadistica_salarial"
    __table_args__ = (UniqueConstraint("fuente", "codigo_ocupacion", "periodo", "medida"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fuente: Mapped[str] = mapped_column(String(32))
    codigo_ocupacion: Mapped[str] = mapped_column(String(32), index=True)  # CNO-11 / ISCO-08
    descripcion: Mapped[str | None] = mapped_column(String(255))
    periodo: Mapped[str] = mapped_column(String(16))
    medida: Mapped[str] = mapped_column(String(64))  # media | mediana | p25 ...
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # El INE marca así las cifras con pocas observaciones (100-500): orientativas.
    precision_baja: Mapped[bool] = mapped_column(Boolean, default=False)


class CorrespondenciaCnoIsco(Base):
    """Correspondencia oficial del INE entre la CNO-11 (España) y la ISCO-08 (CIUO-08).

    ESCO clasifica sus ocupaciones con ISCO-08 y los salarios del INE vienen por CNO-11:
    esta tabla une ambos mundos. Es de muchos a muchos a 4 dígitos.
    """

    __tablename__ = "correspondencia_cno_isco"

    cno: Mapped[str] = mapped_column(String(4), primary_key=True)
    isco: Mapped[str] = mapped_column(String(4), primary_key=True, index=True)
    titulo_cno: Mapped[str] = mapped_column(String(255))
