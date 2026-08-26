import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

EstadoLead = Literal["nuevo", "contactado", "en_negociacion", "convertido", "descartado"]
TipoInteraccion = Literal["llamada", "email", "visita"]


class LeadCreate(BaseModel):
    nombre: str = Field(min_length=1)
    email: EmailStr
    telefono: str = Field(min_length=1)
    sede_interes_id: uuid.UUID
    origen: str = Field(min_length=1)


class LeadUpdate(BaseModel):
    estado: EstadoLead | None = None
    comercial_id: uuid.UUID | None = None


class LeadOut(BaseModel):
    id: uuid.UUID
    nombre: str
    email: str
    telefono: str
    sede_interes_id: uuid.UUID
    origen: str
    estado: str
    comercial_id: uuid.UUID | None
    fecha_creacion: datetime

    model_config = {"from_attributes": True}


class InteraccionLeadCreate(BaseModel):
    tipo: TipoInteraccion
    notas: str = Field(min_length=1)


class InteraccionLeadOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID
    tipo: str
    notas: str
    fecha: datetime
    autor_id: uuid.UUID

    model_config = {"from_attributes": True}


class LeadConvertir(BaseModel):
    """Datos del socio que no existen en el lead (formulario web/manual de
    captación no los recoge) y que son obligatorios en el modelo de Socio (003)."""

    fecha_nacimiento: date
    direccion: str = Field(min_length=1)
    contacto_emergencia_nombre: str = Field(min_length=1)
    contacto_emergencia_telefono: str = Field(min_length=1)
