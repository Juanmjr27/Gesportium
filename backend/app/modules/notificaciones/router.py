from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identidad.dependencies import get_current_user
from app.modules.identidad.models import Usuario
from app.modules.notificaciones import service
from app.modules.notificaciones.models import Notificacion
from app.modules.notificaciones.schemas import (
    NotificacionOut,
    PreferenciaNotificacionOut,
    PreferenciaNotificacionUpdate,
)

router = APIRouter(tags=["notificaciones"])


@router.get("/notificaciones", response_model=list[NotificacionOut])
def historial_notificaciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id == usuario.id)
        .order_by(Notificacion.fecha_creacion.desc())
        .all()
    )


@router.put("/notificaciones/preferencias", response_model=PreferenciaNotificacionOut)
def actualizar_preferencias(
    body: PreferenciaNotificacionUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return service.actualizar_preferencia(db, usuario.id, body.marketing_activo)
