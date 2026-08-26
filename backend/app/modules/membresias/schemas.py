import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TipoDuracion = Literal["mensual", "trimestral", "anual"]
TipoAlcance = Literal["sede_unica", "toda_cadena"]
TipoOrigenCongelacion = Literal["manual", "impago"]


class PlanMembresiaCreate(BaseModel):
    nombre: str = Field(min_length=1)
    precio: Decimal = Field(gt=0)
    duracion: TipoDuracion
    alcance: TipoAlcance
    sede_id: uuid.UUID | None = None
    preaviso_cancelacion_dias: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _validar_sede_segun_alcance(self):
        if self.alcance == "sede_unica" and self.sede_id is None:
            raise ValueError("sede_id es obligatorio cuando el alcance es 'sede_unica'")
        if self.alcance == "toda_cadena" and self.sede_id is not None:
            raise ValueError("sede_id debe ser nulo cuando el alcance es 'toda_cadena'")
        return self


class PlanMembresiaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    precio: Decimal | None = Field(default=None, gt=0)
    preaviso_cancelacion_dias: int | None = Field(default=None, ge=0)
    activo: bool | None = None


class PlanMembresiaOut(BaseModel):
    id: uuid.UUID
    nombre: str
    precio: Decimal
    duracion: str
    alcance: str
    sede_id: uuid.UUID | None
    preaviso_cancelacion_dias: int
    activo: bool

    model_config = {"from_attributes": True}


class MembresiaCreate(BaseModel):
    socio_id: uuid.UUID
    plan_id: uuid.UUID
    fecha_inicio: date | None = None
    renovacion_automatica: bool = True


class HistorialEstadoOut(BaseModel):
    id: uuid.UUID
    estado_anterior: str | None
    estado_nuevo: str
    autor_id: uuid.UUID
    fecha: datetime

    model_config = {"from_attributes": True}


class CongelacionOut(BaseModel):
    id: uuid.UUID
    fecha_inicio: date
    fecha_fin: date | None
    motivo: str | None
    origen: str

    model_config = {"from_attributes": True}


class MembresiaDetail(BaseModel):
    id: uuid.UUID
    socio_id: uuid.UUID
    plan_id: uuid.UUID
    fecha_inicio: date
    fecha_proxima_renovacion: date
    renovacion_automatica: bool
    estado: str
    fecha_cancelacion: date | None

    model_config = {"from_attributes": True}


class CongelarMembresiaBody(BaseModel):
    motivo: str | None = None


class CancelarMembresiaBody(BaseModel):
    motivo: str | None = None
