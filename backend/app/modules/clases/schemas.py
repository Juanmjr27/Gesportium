import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DecisionReasignacion = Literal["reasignar", "cancelar"]


class ClaseCreate(BaseModel):
    sede_id: uuid.UUID
    entrenador_id: uuid.UUID
    nombre: str = Field(min_length=1)
    tipo: str = Field(min_length=1)
    fecha_hora: datetime
    duracion_minutos: int = Field(gt=0)
    aforo_maximo: int = Field(gt=0)
    recurrente: bool = False
    regla_recurrencia: str | None = None


class ClaseUpdate(BaseModel):
    entrenador_id: uuid.UUID | None = None
    nombre: str | None = Field(default=None, min_length=1)
    tipo: str | None = Field(default=None, min_length=1)
    fecha_hora: datetime | None = None
    duracion_minutos: int | None = Field(default=None, gt=0)
    aforo_maximo: int | None = Field(default=None, gt=0)
    recurrente: bool | None = None
    regla_recurrencia: str | None = None


class ClaseListItem(BaseModel):
    id: uuid.UUID
    sede_id: uuid.UUID
    entrenador_id: uuid.UUID
    nombre: str
    tipo: str
    fecha_hora: datetime
    duracion_minutos: int
    aforo_maximo: int
    recurrente: bool
    estado: str

    model_config = {"from_attributes": True}


class ClaseDetail(ClaseListItem):
    regla_recurrencia: str | None
    plazas_disponibles: int
    en_lista_espera: int


class ReservaOut(BaseModel):
    id: uuid.UUID
    clase_id: uuid.UUID
    socio_id: uuid.UUID
    estado: str
    fecha_reserva: datetime
    fecha_cancelacion: datetime | None
    cancelada_fuera_plazo: bool | None

    model_config = {"from_attributes": True}


class OcupacionOut(BaseModel):
    clase_id: uuid.UUID
    aforo_maximo: int
    confirmadas: int
    plazas_disponibles: int
    en_lista_espera: int


class ReasignarPorBajaEntrenadorBody(BaseModel):
    entrenador_id: uuid.UUID
    decision: DecisionReasignacion
    nuevo_entrenador_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _validar_nuevo_entrenador(self):
        if self.decision == "reasignar" and self.nuevo_entrenador_id is None:
            raise ValueError("nuevo_entrenador_id es obligatorio cuando decision='reasignar'")
        if self.decision == "cancelar" and self.nuevo_entrenador_id is not None:
            raise ValueError("nuevo_entrenador_id debe ser nulo cuando decision='cancelar'")
        return self
