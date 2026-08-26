import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Eventos disparadores (spec.md FR3) + "aforo_superado" (aviso interno a
# gestor_sede, gancho ya identificado en accesos/service.py) y "marketing"
# (única categoría que el socio puede desactivar vía PreferenciaNotificacion;
# spec.md: "no las transaccionales"). No hay generador de campañas de
# marketing en este proyecto (spec.md, "Fuera de alcance"): el tipo existe
# para que la preferencia tenga efecto si algún módulo futuro la usa.
TIPOS_NOTIFICACION = (
    "plaza_liberada",
    "clase_reasignada",
    "clase_cancelada",
    "pago_fallido",
    "membresia_proxima_vencer",
    "membresia_vencida",
    "bienvenida",
    "aforo_superado",
    "marketing",
)
CANALES_NOTIFICACION = ("email", "push")
ESTADOS_NOTIFICACION = ("pendiente", "enviada", "fallida")


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    canal: Mapped[str] = mapped_column(String, default="email", nullable=False)
    estado: Mapped[str] = mapped_column(String, default="pendiente", nullable=False)
    intentos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Fuera del esquema literal de plan.md (que solo lista tipo/canal/estado):
    # se guarda el contenido ya renderizado en el momento de encolar (en vez
    # de recalcularlo al enviar), para que el historial (FR6) muestre el
    # texto real enviado aunque la plantilla cambie después.
    asunto: Mapped[str] = mapped_column(String, nullable=False)
    cuerpo: Mapped[str] = mapped_column(String, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_envio: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PreferenciaNotificacion(Base):
    __tablename__ = "preferencias_notificacion"

    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), primary_key=True)
    marketing_activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
