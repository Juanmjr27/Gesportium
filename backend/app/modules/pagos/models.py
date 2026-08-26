import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ESTADOS_PAGO = ("exitoso", "fallido", "pendiente")


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    socio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("socios.id"), nullable=False)
    membresia_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("membresias.id"), nullable=True)
    concepto: Mapped[str] = mapped_column(String, nullable=False)
    importe: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String, default="pendiente", nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    # Campos fuera del esquema literal de plan.md, añadidos para poder
    # implementar sin ambigüedad los criterios de aceptación de la spec:
    # - intentos: cuenta los reintentos de cobro (T4/T8), en vez de crear
    #   una fila de Pago nueva por cada intento fallido.
    intentos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # - periodo: identifica el ciclo de renovación facturado, para poder
    #   aplicar el criterio "no se puede facturar dos veces el mismo
    #   periodo" (nulo para pagos no ligados a una renovación de membresía).
    periodo: Mapped[date | None] = mapped_column(Date, nullable=True)


class Factura(Base):
    __tablename__ = "facturas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pago_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pagos.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    pdf_url: Mapped[str] = mapped_column(String, nullable=False)
    fecha_emision: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    anulada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Remesa(Base):
    __tablename__ = "remesas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sede_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sedes.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


class RemesaPago(Base):
    __tablename__ = "remesa_pagos"

    remesa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("remesas.id"), primary_key=True)
    pago_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pagos.id"), primary_key=True)


# Trazabilidad de Pago/Factura/Remesa (y, por extensión, de las filas de
# RemesaPago que se crean junto con su Remesa): mismo patrón de auditoría
# que historial_acciones_socio (003) e historial_estados_membresia (004),
# pero polimórfico (entidad_tipo + entidad_id) porque aquí son varias
# entidades relacionadas en vez de una sola.
ENTIDADES_HISTORIAL_PAGO = ("pago", "factura", "remesa")


class HistorialAccionPago(Base):
    __tablename__ = "historial_acciones_pago"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entidad_tipo: Mapped[str] = mapped_column(String, nullable=False)
    entidad_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    accion: Mapped[str] = mapped_column(String, nullable=False)
    autor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
