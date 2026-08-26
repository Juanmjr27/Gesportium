import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.modules.clases import service as clases_service
from app.modules.entrenadores.models import Entrenador, SocioAsignado


def ids_socios_asignados(db: Session, usuario_id: uuid.UUID) -> list[uuid.UUID]:
    entrenador = db.query(Entrenador).filter(Entrenador.usuario_id == usuario_id).first()
    if entrenador is None:
        return []
    asignaciones = (
        db.query(SocioAsignado.socio_id)
        .filter(SocioAsignado.entrenador_id == entrenador.id, SocioAsignado.fecha_fin.is_(None))
        .all()
    )
    return [socio_id for (socio_id,) in asignaciones]


def asignar_socio(db: Session, entrenador_id: uuid.UUID, socio_id: uuid.UUID) -> SocioAsignado:
    asignacion = SocioAsignado(entrenador_id=entrenador_id, socio_id=socio_id)
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    return asignacion


def desasignar_socio(db: Session, asignacion: SocioAsignado) -> SocioAsignado:
    asignacion.fecha_fin = date.today()
    db.commit()
    db.refresh(asignacion)
    return asignacion


def dar_baja_entrenador(
    db: Session,
    entrenador: Entrenador,
    decision: str | None,
    nuevo_entrenador_id: uuid.UUID | None,
) -> Entrenador:
    entrenador.activo = False

    # Dependencia con el módulo 005 (plan.md Fase 2): si tiene clases futuras
    # activas, se reasignan o cancelan aquí mismo (contrato interno de
    # servicio equivalente a POST /clases/reasignar-por-baja-entrenador).
    if clases_service.listar_clases_futuras_activas(db, entrenador.id):
        clases_service.reasignar_por_baja_entrenador(db, entrenador.id, decision, nuevo_entrenador_id)

    db.commit()
    db.refresh(entrenador)
    return entrenador
