import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.modules.notificaciones import service as notificaciones_service
from app.modules.socios.models import HistorialAccionSocio, HistorialSedesSocio, Socio
from app.modules.socios.schemas import SocioCreate


def obtener_socio(db: Session, socio_id: uuid.UUID) -> Socio | None:
    return db.get(Socio, socio_id)


def obtener_socio_por_usuario(db: Session, usuario_id: uuid.UUID) -> Socio | None:
    return db.query(Socio).filter(Socio.usuario_id == usuario_id).first()


def tiene_socios_activos(db: Session, sede_id: uuid.UUID) -> bool:
    return db.query(Socio).filter(Socio.sede_id == sede_id, Socio.activo.is_(True)).first() is not None


def ids_socios_por_sede(db: Session, sede_id: uuid.UUID) -> list[uuid.UUID]:
    ids = db.query(Socio.id).filter(Socio.sede_id == sede_id).all()
    return [socio_id for (socio_id,) in ids]


def crear_socio(db: Session, body: SocioCreate, autor_id: uuid.UUID) -> Socio:
    socio = Socio(**body.model_dump())
    db.add(socio)
    db.flush()

    db.add(HistorialSedesSocio(socio_id=socio.id, sede_id=socio.sede_id, fecha_inicio=date.today(), fecha_fin=None))
    db.add(HistorialAccionSocio(socio_id=socio.id, accion="alta", autor_id=autor_id))
    db.commit()
    db.refresh(socio)

    notificaciones_service.encolar_notificacion(db, socio.usuario_id, "bienvenida")
    return socio


def dar_baja_socio(db: Session, socio: Socio, autor_id: uuid.UUID) -> Socio:
    socio.activo = False
    socio.fecha_baja = date.today()
    db.add(HistorialAccionSocio(socio_id=socio.id, accion="baja", autor_id=autor_id))
    db.commit()
    db.refresh(socio)
    return socio


def transferir_socio(db: Session, socio: Socio, nueva_sede_id: uuid.UUID) -> Socio:
    hoy = date.today()

    historial_actual = (
        db.query(HistorialSedesSocio)
        .filter(HistorialSedesSocio.socio_id == socio.id, HistorialSedesSocio.fecha_fin.is_(None))
        .first()
    )
    if historial_actual is not None:
        historial_actual.fecha_fin = hoy

    db.add(HistorialSedesSocio(socio_id=socio.id, sede_id=nueva_sede_id, fecha_inicio=hoy, fecha_fin=None))
    socio.sede_id = nueva_sede_id

    db.commit()
    db.refresh(socio)
    return socio
