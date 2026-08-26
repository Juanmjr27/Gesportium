import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

DiaSemana = Literal["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


class EjercicioCreate(BaseModel):
    nombre: str = Field(min_length=1)
    series: int = Field(gt=0)
    repeticiones: int = Field(gt=0)
    dia_semana: DiaSemana
    descanso_segundos: int = Field(ge=0)


class EjercicioOut(BaseModel):
    id: uuid.UUID
    nombre: str
    series: int
    repeticiones: int
    dia_semana: str
    descanso_segundos: int

    model_config = {"from_attributes": True}


class RutinaCreate(BaseModel):
    socio_id: uuid.UUID
    nombre: str = Field(min_length=1)
    ejercicios: list[EjercicioCreate] = Field(min_length=1)


class RutinaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    activa: bool | None = None


class RutinaOut(BaseModel):
    id: uuid.UUID
    entrenador_id: uuid.UUID
    socio_id: uuid.UUID
    nombre: str
    activa: bool
    fecha_creacion: date
    origen: str
    borrador_id: uuid.UUID | None
    ejercicios: list[EjercicioOut] = []

    model_config = {"from_attributes": True}


class PlanNutricionalCreate(BaseModel):
    socio_id: uuid.UUID
    nombre: str = Field(min_length=1)
    notas: str | None = None


class PlanNutricionalUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1)
    notas: str | None = None
    activo: bool | None = None


class PlanNutricionalOut(BaseModel):
    id: uuid.UUID
    entrenador_id: uuid.UUID
    socio_id: uuid.UUID
    nombre: str
    activo: bool
    notas: str | None
    origen: str
    borrador_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class CompletarEjercicioBody(BaseModel):
    ejercicio_id: uuid.UUID
    fecha: date = Field(default_factory=date.today)
    completado: bool = True


class CumplimientoOut(BaseModel):
    id: uuid.UUID
    ejercicio_id: uuid.UUID
    socio_id: uuid.UUID
    fecha: date
    completado: bool

    model_config = {"from_attributes": True}
