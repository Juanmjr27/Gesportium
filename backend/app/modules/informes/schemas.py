import uuid
from datetime import date, datetime

from pydantic import BaseModel

TIPOS_INFORME = ("socios", "financiero", "ocupacion", "comercial")


class DetalleAltaBajaSocio(BaseModel):
    socio_id: uuid.UUID
    email: str
    accion: str
    fecha: datetime


class InformeSociosOut(BaseModel):
    sede_id: uuid.UUID | None
    fecha_inicio: date
    fecha_fin: date
    total_altas: int
    total_bajas: int
    socios_activos_al_cierre: int
    detalle: list[DetalleAltaBajaSocio]
    resumen_ia: str | None = None


class DetallePagoInforme(BaseModel):
    pago_id: uuid.UUID
    socio_id: uuid.UUID
    email: str
    concepto: str
    importe: float
    estado: str
    fecha: datetime


class InformeFinancieroOut(BaseModel):
    sede_id: uuid.UUID | None
    fecha_inicio: date
    fecha_fin: date
    total_ingresos: float
    total_impagos: float
    detalle: list[DetallePagoInforme]
    resumen_ia: str | None = None


class DetalleClaseInforme(BaseModel):
    clase_id: uuid.UUID
    nombre: str
    fecha_hora: datetime
    aforo_maximo: int
    reservas_confirmadas: int
    ocupacion_pct: float


class InformeOcupacionOut(BaseModel):
    sede_id: uuid.UUID | None
    fecha_inicio: date
    fecha_fin: date
    ocupacion_media_pct: float
    detalle: list[DetalleClaseInforme]
    resumen_ia: str | None = None


class DetalleLeadInforme(BaseModel):
    lead_id: uuid.UUID
    nombre: str
    origen: str
    estado: str
    fecha_creacion: datetime


class InformeComercialOut(BaseModel):
    sede_id: uuid.UUID | None
    fecha_inicio: date
    fecha_fin: date
    total_leads: int
    convertidos: int
    tasa_conversion_pct: float
    detalle: list[DetalleLeadInforme]
    resumen_ia: str | None = None
