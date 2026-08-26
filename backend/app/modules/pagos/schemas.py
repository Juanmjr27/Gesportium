import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class PagoOut(BaseModel):
    id: uuid.UUID
    socio_id: uuid.UUID
    membresia_id: uuid.UUID | None
    concepto: str
    importe: Decimal
    estado: str
    fecha: datetime
    intentos: int
    # No es un atributo de Pago (construido aparte en el router vía join con
    # Factura): permite al portal de socio (specs/015) descargar la factura
    # de un pago sin necesitar un endpoint de listado de facturas.
    factura_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class FacturaOut(BaseModel):
    id: uuid.UUID
    pago_id: uuid.UUID
    numero: str
    fecha_emision: datetime
    anulada: bool

    model_config = {"from_attributes": True}


class RemesaCreate(BaseModel):
    sede_id: uuid.UUID
    fecha: date


class RemesaOut(BaseModel):
    id: uuid.UUID
    sede_id: uuid.UUID
    fecha: date
    total: Decimal
    pagos_incluidos: int
