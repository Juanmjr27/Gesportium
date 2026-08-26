import uuid
from datetime import datetime
 
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
 
from app.core.database import Base
 
ROLES_MENSAJE = ("socio", "asistente")
TIPOS_BORRADOR = ("rutina", "plan_nutricional")
ESTADOS_BORRADOR = ("pendiente", "aprobado", "rechazado")
 
 
class ConversacionIA(Base):
    __tablename__ = "conversaciones_ia"
 
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
 
 
class MensajeIA(Base):
    __tablename__ = "mensajes_ia"
 
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversaciones_ia.id"), nullable=False
    )
    rol: Mapped[str] = mapped_column(String, nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
 
 
class BorradorIA(Base):
    __tablename__ = "borradores_ia"
 
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    datos_cuestionario: Mapped[dict] = mapped_column(JSONB, nullable=False)
    contenido: Mapped[dict] = mapped_column(JSONB, nullable=False)
    estado: Mapped[str] = mapped_column(String, default="pendiente", nullable=False)
    entrenador_revisor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entrenadores.id"), nullable=True
    )
    fecha_revision: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    motivo_rechazo: Mapped[str | None] = mapped_column(Text, nullable=True)