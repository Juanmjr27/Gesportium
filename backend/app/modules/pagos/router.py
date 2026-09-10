import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identidad.dependencies import require_roles, verificar_acceso_por_sede
from app.modules.identidad.models import Usuario
from app.modules.pagos import service
from app.modules.pagos.models import Factura, Pago, Remesa, RemesaPago
from app.modules.pagos.schemas import FacturaOut, PagoOut, RemesaCreate, RemesaOut
from app.modules.sedes.models import Sede
from app.modules.socios.models import Socio

router = APIRouter(tags=["pagos"])


def _construir_remesa_out(db: Session, remesa: Remesa) -> RemesaOut:
    pagos_incluidos = db.query(RemesaPago).filter(RemesaPago.remesa_id == remesa.id).count()
    return RemesaOut(id=remesa.id, sede_id=remesa.sede_id, fecha=remesa.fecha, total=remesa.total, pagos_incluidos=pagos_incluidos)


def _construir_pago_out(db: Session, pago: Pago) -> PagoOut:
    # Una factura anulada se reemite como una fila nueva (service.py:60-73),
    # así que la "vigente" es la no anulada más reciente; si todas están
    # anuladas y aún no se ha reemitido, no hay nada descargable.
    factura_vigente = (
        db.query(Factura)
        .filter(Factura.pago_id == pago.id, Factura.anulada.is_(False))
        .order_by(Factura.fecha_emision.desc())
        .first()
    )
    datos = PagoOut.model_validate(pago).model_dump()
    datos["factura_id"] = factura_vigente.id if factura_vigente else None
    return PagoOut(**datos)


@router.get("/pagos/{socio_id}", response_model=list[PagoOut])
def historial_pagos(
    socio_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "socio")),
):
    socio = db.get(Socio, socio_id)
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")
    verificar_acceso_por_sede(usuario, socio.sede_id, propietario_id=socio.usuario_id, rol_propietario="socio")

    pagos = db.query(Pago).filter(Pago.socio_id == socio_id).order_by(Pago.fecha.desc()).all()
    return [_construir_pago_out(db, pago) for pago in pagos]


@router.get("/facturas/{factura_id}")
def descargar_factura(
    factura_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "socio")),
):
    factura = db.get(Factura, factura_id)
    if factura is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")

    pago = db.get(Pago, factura.pago_id)
    socio = db.get(Socio, pago.socio_id)
    verificar_acceso_por_sede(usuario, socio.sede_id, propietario_id=socio.usuario_id, rol_propietario="socio")

    return FileResponse(factura.pdf_url, media_type="application/pdf", filename=f"{factura.numero}.pdf")


@router.post("/facturas/{factura_id}/anular", response_model=FacturaOut)
def anular_factura(
    factura_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    factura = db.get(Factura, factura_id)
    if factura is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")

    pago = db.get(Pago, factura.pago_id)
    socio = db.get(Socio, pago.socio_id)
    verificar_acceso_por_sede(usuario, socio.sede_id, propietario_id=socio.usuario_id, rol_propietario="socio")

    try:
        return service.anular_factura(db, factura, autor_id=usuario.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/facturas/{factura_id}/reemitir", response_model=FacturaOut, status_code=status.HTTP_201_CREATED)
def reemitir_factura(
    factura_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    factura = db.get(Factura, factura_id)
    if factura is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")

    pago = db.get(Pago, factura.pago_id)
    socio = db.get(Socio, pago.socio_id)
    verificar_acceso_por_sede(usuario, socio.sede_id, propietario_id=socio.usuario_id, rol_propietario="socio")

    try:
        return service.reemitir_factura(db, factura, autor_id=usuario.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/remesas", response_model=RemesaOut, status_code=status.HTTP_201_CREATED)
def crear_remesa(
    body: RemesaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    if usuario.rol == "gestor_sede" and usuario.sede_id != body.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta sede")

    if db.get(Sede, body.sede_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    remesa = service.generar_remesa(db, body.sede_id, body.fecha, autor_id=usuario.id)
    return _construir_remesa_out(db, remesa)


@router.get("/remesas", response_model=list[RemesaOut])
def listar_remesas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    query = db.query(Remesa)
    if usuario.rol == "gestor_sede":
        query = query.filter(Remesa.sede_id == usuario.sede_id)
    return [_construir_remesa_out(db, r) for r in query.all()]
