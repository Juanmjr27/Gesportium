import uuid
from datetime import datetime, time

from pydantic import BaseModel, Field


class SedeCreate(BaseModel):
    nombre: str = Field(min_length=1)
    direccion: str = Field(min_length=1)
    ciudad: str = Field(min_length=1)
    telefono: str = Field(min_length=1)
    horario_apertura: time
    horario_cierre: time
    aforo_maximo: int = Field(gt=0)


class SedeUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    direccion: str | None = Field(default=None, min_length=1)
    ciudad: str | None = Field(default=None, min_length=1)
    telefono: str | None = Field(default=None, min_length=1)
    horario_apertura: time | None = None
    horario_cierre: time | None = None
    aforo_maximo: int | None = Field(default=None, gt=0)


class SedePublic(BaseModel):
    id: uuid.UUID
    nombre: str
    direccion: str
    ciudad: str
    horario_apertura: time
    horario_cierre: time

    model_config = {"from_attributes": True}


class SedeDetail(BaseModel):
    id: uuid.UUID
    nombre: str
    direccion: str
    ciudad: str
    telefono: str
    horario_apertura: time
    horario_cierre: time
    aforo_maximo: int
    activa: bool
    fecha_creacion: datetime

    model_config = {"from_attributes": True}
