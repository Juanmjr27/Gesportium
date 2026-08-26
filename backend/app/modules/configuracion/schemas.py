import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ConfiguracionOut(BaseModel):
    clave: str
    valor: str
    tipo: str

    model_config = {"from_attributes": True}


class ConfiguracionUpdate(BaseModel):
    valor: str = Field(min_length=1)


class HistorialConfiguracionOut(BaseModel):
    id: uuid.UUID
    clave: str
    valor_anterior: str
    valor_nuevo: str
    autor_id: uuid.UUID
    fecha: datetime

    model_config = {"from_attributes": True}
