import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DURACIONES = ("mensual", "trimestral", "anual")
ALCANCES = ("sede_unica", "toda_cadena")
ESTADOS_MEMBRESIA = ("activa", "congelada", "cancelada", "vencida")
ORIGENES_CONGELACION = ("manual", "impago")


class PlanMembresia(Base):
    __tablename__ = "planes_membresia"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duracion: Mapped[str] = mapped_column(String, nullable=False)
    alcance: Mapped[str] = mapped_column(String, nullable=False)
    sede_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sedes.id"), nullable=True)
    preaviso_cancelacion_dias: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Membresia(Base):
    __tablename__ = "membresias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("planes_membresia.id"), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_proxima_renovacion: Mapped[date] = mapped_column(Date, nullable=False)
    renovacion_automatica: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    estado: Mapped[str] = mapped_column(String, default="activa", nullable=False)
    fecha_cancelacion: Mapped[date | None] = mapped_column(Date, nullable=True)


class CongelacionMembresia(Base):
    __tablename__ = "congelaciones_membresia"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    membresia_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("membresias.id"), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    motivo: Mapped[str | None] = mapped_column(String, nullable=True)
    origen: Mapped[str] = mapped_column(String, default="manual", nullable=False)


class HistorialEstadosMembresia(Base):
    __tablename__ = "historial_estados_membresia"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    membresia_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("membresias.id"), nullable=False)
    estado_anterior: Mapped[str | None] = mapped_column(String, nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String, nullable=False)
    autor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
