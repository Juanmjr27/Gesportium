import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificacionOut(BaseModel):
    id: uuid.UUID
    tipo: str
    canal: str
    estado: str
    intentos: int
    asunto: str
    fecha_creacion: datetime
    fecha_envio: datetime | None

    model_config = {"from_attributes": True}


class PreferenciaNotificacionOut(BaseModel):
    usuario_id: uuid.UUID
    marketing_activo: bool

    model_config = {"from_attributes": True}


class PreferenciaNotificacionUpdate(BaseModel):
    marketing_activo: bool
