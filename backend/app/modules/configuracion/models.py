import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

TIPOS_CONFIGURACION = ("texto", "numero", "booleano")


class ConfiguracionGlobal(Base):
    __tablename__ = "configuracion_global"

    clave: Mapped[str] = mapped_column(String, primary_key=True)
    valor: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)


class HistorialConfiguracion(Base):
    __tablename__ = "historial_configuracion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clave: Mapped[str] = mapped_column(String, ForeignKey("configuracion_global.clave"), nullable=False)
    valor_anterior: Mapped[str] = mapped_column(String, nullable=False)
    valor_nuevo: Mapped[str] = mapped_column(String, nullable=False)
    autor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
