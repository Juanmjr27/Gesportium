import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.accesos import service
from app.modules.accesos.dependencies import require_totem_device
from app.modules.accesos.models import Acceso
from app.modules.accesos.schemas import AccesoCheckinRequest, AccesoOut, AforoActualOut
from app.modules.identidad.dependencies import require_roles
from app.modules.identidad.models import Usuario
from app.modules.sedes.models import Sede
from app.modules.socios.models import Socio

router = APIRouter(tags=["accesos"])


@router.post("/accesos/checkin", response_model=AccesoOut, status_code=status.HTTP_201_CREATED)
def checkin(
    body: AccesoCheckinRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_totem_device),
):
    if db.get(Socio, body.socio_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")
    if db.get(Sede, body.sede_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    try:
        return service.registrar_checkin(db, body.socio_id, body.sede_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("/sedes/{sede_id}/aforo-actual", response_model=AforoActualOut)
def aforo_actual(
    sede_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede")),
):
    sede = db.get(Sede, sede_id)
    if sede is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")
    if usuario.rol == "gestor_sede" and usuario.sede_id != sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre esta sede")

    return service.calcular_aforo_actual(db, sede)


@router.get("/accesos/{socio_id}", response_model=list[AccesoOut])
def historial_accesos(
    socio_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("admin", "gestor_sede", "socio")),
):
    socio = db.get(Socio, socio_id)
    if socio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Socio no encontrado")

    if usuario.rol == "gestor_sede" and usuario.sede_id != socio.sede_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este socio")
    if usuario.rol == "socio" and usuario.id != socio.usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este socio")

    return db.query(Acceso).filter(Acceso.socio_id == socio_id).order_by(Acceso.fecha_hora.desc()).all()
