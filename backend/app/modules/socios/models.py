import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Socio(Base):
    __tablename__ = "socios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False
    )
    sede_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sedes.id"), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    telefono: Mapped[str] = mapped_column(String, nullable=False)
    direccion: Mapped[str] = mapped_column(String, nullable=False)
    contacto_emergencia_nombre: Mapped[str] = mapped_column(String, nullable=False)
    contacto_emergencia_telefono: Mapped[str] = mapped_column(String, nullable=False)
    fecha_alta: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    fecha_baja: Mapped[date | None] = mapped_column(Date, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DocumentoSocio(Base):
    __tablename__ = "documentos_socio"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    archivo_url: Mapped[str] = mapped_column(String, nullable=False)
    fecha_subida: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_caducidad: Mapped[date | None] = mapped_column(Date, nullable=True)


class NotaSocio(Base):
    __tablename__ = "notas_socio"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    autor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class HistorialSedesSocio(Base):
    __tablename__ = "historial_sedes_socio"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    sede_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sedes.id"), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)


ACCIONES_SOCIO = ("alta", "baja")


class HistorialAccionSocio(Base):
    __tablename__ = "historial_acciones_socio"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    accion: Mapped[str] = mapped_column(String, nullable=False)
    autor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
