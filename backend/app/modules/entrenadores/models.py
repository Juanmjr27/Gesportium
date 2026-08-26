import uuid
from datetime import date

from sqlalchemy import ARRAY, Boolean, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Entrenador(Base):
    __tablename__ = "entrenadores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False
    )
    sede_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sedes.id"), nullable=False)
    especialidades: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    horario_disponible: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SocioAsignado(Base):
    __tablename__ = "socios_asignados"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entrenador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entrenadores.id"), nullable=False)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
