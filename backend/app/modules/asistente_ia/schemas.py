import uuid
from datetime import datetime
from typing import Literal
 
from pydantic import BaseModel, Field, model_validator
 
 
class MensajeCreate(BaseModel):
    contenido: str = Field(min_length=1)
 
 
class MensajeOut(BaseModel):
    id: uuid.UUID
    conversacion_id: uuid.UUID
    rol: str
    contenido: str
    fecha: datetime
 
    model_config = {"from_attributes": True}
 
 
class WizardBorradorRequest(BaseModel):
    """Payload completo del cuestionario guiado (spec 016, pasos 0-4)."""
 
    # Paso 0
    tipo_borrador: Literal["rutina", "plan_nutricional"]
 
    # Paso 2 — datos físicos
    sexo: Literal["masculino", "femenino", "prefiero_no_decirlo"]
    peso_kg: float = Field(ge=20, le=300)
    altura_cm: float = Field(ge=100, le=250)
    nivel_actividad_actual: Literal["sedentario", "activo", "muy_activo"] | None = None
    restricciones_medicas: str | None = None
 
    # Paso 3 — preferencias (condicionadas por tipo_borrador)
    dias_disponibles_semana: int | None = Field(default=None, ge=1, le=7)
    equipamiento: Literal["gimnasio_completo", "casa_basico", "sin_material"] | None = None
    lesiones_zonas_evitar: str | None = None
 
    preferencia_alimentaria: Literal["omnivoro", "vegetariano", "vegano", "otro"] | None = None
    comidas_al_dia: int | None = Field(default=None, ge=2, le=6)
    alimentos_excluir: str | None = None
 
    # Paso 4 — objetivo
    objetivo_principal: Literal[
        "perder_peso", "ganar_masa_muscular", "mantenimiento", "rendimiento_deportivo", "salud_general"
    ]
    objetivo_detalle: str | None = Field(default=None, max_length=280)
 
    @model_validator(mode="after")
    def campos_obligatorios_segun_tipo(self) -> "WizardBorradorRequest":
        if self.tipo_borrador == "rutina":
            faltan = [
                nombre
                for nombre, valor in (
                    ("nivel_actividad_actual", self.nivel_actividad_actual),
                    ("dias_disponibles_semana", self.dias_disponibles_semana),
                    ("equipamiento", self.equipamiento),
                )
                if valor is None
            ]
            if faltan:
                raise ValueError(f"Campos obligatorios para tipo_borrador=rutina: {', '.join(faltan)}")
        else:  # plan_nutricional
            faltan = [
                nombre
                for nombre, valor in (
                    ("preferencia_alimentaria", self.preferencia_alimentaria),
                    ("comidas_al_dia", self.comidas_al_dia),
                )
                if valor is None
            ]
            if faltan:
                raise ValueError(f"Campos obligatorios para tipo_borrador=plan_nutricional: {', '.join(faltan)}")
        return self
 
 
class BorradorOut(BaseModel):
    id: uuid.UUID
    socio_id: uuid.UUID
    tipo: str
    datos_cuestionario: dict
    contenido: dict
    estado: str
    entrenador_revisor_id: uuid.UUID | None
    fecha_revision: datetime | None
    motivo_rechazo: str | None
 
    model_config = {"from_attributes": True}
 
 
class BorradorEditar(BaseModel):
    """Body de PATCH /asistente/borradores/{id} — el entrenador edita el
    borrador antes de aprobarlo. No cambia `estado`."""
 
    contenido: dict
 
 
class BorradorRechazar(BaseModel):
    motivo: str = Field(min_length=1)