import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ESTADOS_CLASE = ("activa", "cancelada")
ESTADOS_RESERVA = ("confirmada", "lista_espera", "cancelada")


class Clase(Base):
    __tablename__ = "clases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sede_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sedes.id"), nullable=False)
    entrenador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entrenadores.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duracion_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    aforo_maximo: Mapped[int] = mapped_column(Integer, nullable=False)
    recurrente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    regla_recurrencia: Mapped[str | None] = mapped_column(String, nullable=True)
    estado: Mapped[str] = mapped_column(String, default="activa", nullable=False)


class Reserva(Base):
    __tablename__ = "reservas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clase_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clases.id"), nullable=False)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String, default="confirmada", nullable=False)
    fecha_reserva: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_cancelacion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Registrado en el momento de cancelar (no recalculado luego), para que
    # cambios posteriores en clase.fecha_hora no alteren el historial: base
    # para futuras políticas de penalización (criterio de aceptación, spec.md).
    cancelada_fuera_plazo: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class Asistencia(Base):
    __tablename__ = "asistencias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reserva_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reservas.id"), nullable=False)
    fecha_checkin: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
