import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

TIPOS_ACCESO = ("entrada", "salida")


class Acceso(Base):
    __tablename__ = "accesos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    sede_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sedes.id"), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
