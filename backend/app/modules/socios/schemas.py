import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.modules.entrenamiento.schemas import PlanNutricionalOut, RutinaOut
from app.modules.membresias.schemas import MembresiaDetail

TIPOS_DOCUMENTO = Literal["consentimiento", "aptitud_medica"]


class SocioCreate(BaseModel):
    usuario_id: uuid.UUID
    sede_id: uuid.UUID
    fecha_nacimiento: date
    telefono: str = Field(min_length=1)
    direccion: str = Field(min_length=1)
    contacto_emergencia_nombre: str = Field(min_length=1)
    contacto_emergencia_telefono: str = Field(min_length=1)


class SocioUpdate(BaseModel):
    fecha_nacimiento: date | None = None
    telefono: str | None = Field(default=None, min_length=1)
    direccion: str | None = Field(default=None, min_length=1)
    contacto_emergencia_nombre: str | None = Field(default=None, min_length=1)
    contacto_emergencia_telefono: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _rechazar_null_explicito(self) -> "SocioUpdate":
        """Todos los campos son NOT NULL en BD (models.py): son opcionales aquí
        solo para permitir omitirlos en un update parcial (router.py usa
        `model_dump(exclude_unset=True)`), no para poder vaciarlos. Sin este
        chequeo, un campo enviado explícitamente como null pasa la validación
        y revienta en la BD con un 500 en vez de un 422."""
        enviados_como_null = [campo for campo in self.model_fields_set if getattr(self, campo) is None]
        if enviados_como_null:
            raise ValueError(f"Los campos {', '.join(sorted(enviados_como_null))} no admiten valor null (omítelos para no modificarlos)")
        return self


# Campos que el propio socio puede editar de sus datos de contacto (FR7).
# `fecha_nacimiento` se incluye porque el wizard del asistente IA (016,
# Paso 1) permite rellenarla cuando falta, guardándola vía este mismo
# endpoint (no crea uno nuevo).
CAMPOS_EDITABLES_PROPIO_SOCIO = {
    "fecha_nacimiento",
    "telefono",
    "direccion",
    "contacto_emergencia_nombre",
    "contacto_emergencia_telefono",
}


class CandidatoSocioOut(BaseModel):
    id: uuid.UUID
    email: str


class SocioListItem(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    email: str
    sede_id: uuid.UUID
    activo: bool
    fecha_alta: date

    model_config = {"from_attributes": True}


class NotaSocioOut(BaseModel):
    id: uuid.UUID
    autor_id: uuid.UUID
    contenido: str
    fecha: datetime

    model_config = {"from_attributes": True}


class SocioSelf(BaseModel):
    """Vista del propio socio: sin notas internas ni historial administrativo (FR7)."""

    id: uuid.UUID
    usuario_id: uuid.UUID
    sede_id: uuid.UUID
    fecha_nacimiento: date
    telefono: str
    direccion: str
    contacto_emergencia_nombre: str
    contacto_emergencia_telefono: str
    fecha_alta: date
    activo: bool

    model_config = {"from_attributes": True}


class SocioDetail(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    sede_id: uuid.UUID
    fecha_nacimiento: date
    telefono: str
    direccion: str
    contacto_emergencia_nombre: str
    contacto_emergencia_telefono: str
    fecha_alta: date
    fecha_baja: date | None
    activo: bool
    notas: list[NotaSocioOut] = []

    model_config = {"from_attributes": True}


class DocumentoSocioCreate(BaseModel):
    tipo: TIPOS_DOCUMENTO
    archivo_url: str = Field(min_length=1)
    fecha_caducidad: date | None = None


class DocumentoSocioOut(BaseModel):
    id: uuid.UUID
    tipo: str
    archivo_url: str
    fecha_subida: datetime
    fecha_caducidad: date | None

    model_config = {"from_attributes": True}


class SocioTransferir(BaseModel):
    nueva_sede_id: uuid.UUID


class NotaSocioCreate(BaseModel):
    contenido: str = Field(min_length=1)


class EntrenadorAsignadoOut(BaseModel):
    id: uuid.UUID
    email: str
    especialidades: list[str]

    model_config = {"from_attributes": True}


class SocioFichaOut(BaseModel):
    """Ficha de socio (specs/017 FR8): agrega datos ya definidos en 003/004/006/007
    sin duplicar su lógica de negocio. Nunca incluye notas internas (003)."""

    id: uuid.UUID
    usuario_id: uuid.UUID
    sede_id: uuid.UUID
    fecha_nacimiento: date
    telefono: str
    direccion: str
    contacto_emergencia_nombre: str
    contacto_emergencia_telefono: str
    fecha_alta: date
    activo: bool
    membresia: MembresiaDetail | None = None
    entrenador_asignado: EntrenadorAsignadoOut | None = None
    rutinas: list[RutinaOut] = []
    planes_nutricionales: list[PlanNutricionalOut] = []

    model_config = {"from_attributes": True}
