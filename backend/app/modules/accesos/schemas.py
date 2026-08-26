import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AccesoCheckinRequest(BaseModel):
    socio_id: uuid.UUID
    sede_id: uuid.UUID


class AccesoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    socio_id: uuid.UUID
    sede_id: uuid.UUID
    fecha_hora: datetime
    tipo: str


class AforoActualOut(BaseModel):
    sede_id: uuid.UUID
    ocupacion_actual: int
    aforo_maximo: int
    aforo_superado: bool
