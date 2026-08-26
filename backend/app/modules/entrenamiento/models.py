import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ORIGENES = ("manual", "ia")
DIAS_SEMANA = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")


class Rutina(Base):
    __tablename__ = "rutinas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entrenador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entrenadores.id"), nullable=False)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    origen: Mapped[str] = mapped_column(String, default="manual", nullable=False)
    borrador_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("borradores_ia.id"), nullable=True
    )


class EjercicioRutina(Base):
    __tablename__ = "ejercicios_rutina"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rutina_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rutinas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    series: Mapped[int] = mapped_column(Integer, nullable=False)
    repeticiones: Mapped[int] = mapped_column(Integer, nullable=False)
    dia_semana: Mapped[str] = mapped_column(String, nullable=False)
    descanso_segundos: Mapped[int] = mapped_column(Integer, nullable=False)


class PlanNutricional(Base):
    __tablename__ = "planes_nutricionales"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entrenador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entrenadores.id"), nullable=False)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    origen: Mapped[str] = mapped_column(String, default="manual", nullable=False)
    borrador_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("borradores_ia.id"), nullable=True
    )


class CumplimientoRutina(Base):
    __tablename__ = "cumplimiento_rutina"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ejercicio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ejercicios_rutina.id"), nullable=False)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    completado: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
