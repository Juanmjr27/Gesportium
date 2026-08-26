import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

DecisionBajaEntrenador = Literal["reasignar", "cancelar"]


class EntrenadorCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    sede_id: uuid.UUID
    especialidades: list[str] = Field(default_factory=list)
    horario_disponible: dict | None = None


class EntrenadorUpdate(BaseModel):
    especialidades: list[str] | None = None
    horario_disponible: dict | None = None


class EntrenadorOut(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    sede_id: uuid.UUID
    especialidades: list[str]
    horario_disponible: dict | None
    activo: bool

    model_config = {"from_attributes": True}


class EntrenadorListItem(EntrenadorOut):
    email: str


class SocioAsignadoCreate(BaseModel):
    socio_id: uuid.UUID


class SocioAsignadoOut(BaseModel):
    id: uuid.UUID
    entrenador_id: uuid.UUID
    socio_id: uuid.UUID
    fecha_inicio: date
    fecha_fin: date | None

    model_config = {"from_attributes": True}


class BajaEntrenadorBody(BaseModel):
    confirmar: bool = False
    decision: DecisionBajaEntrenador | None = None
    nuevo_entrenador_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _validar_decision(self):
        if self.decision == "reasignar" and self.nuevo_entrenador_id is None:
            raise ValueError("nuevo_entrenador_id es obligatorio cuando decision='reasignar'")
        if self.decision == "cancelar" and self.nuevo_entrenador_id is not None:
            raise ValueError("nuevo_entrenador_id debe ser nulo cuando decision='cancelar'")
        return self


class ClaseFuturaAfectadaOut(BaseModel):
    id: uuid.UUID
    nombre: str
    fecha_hora: datetime

    model_config = {"from_attributes": True}
