import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.modules.accesos.models import Acceso
from app.modules.clases import service as clases_service
from app.modules.clases.models import Asistencia, Clase, Reserva
from app.modules.identidad.models import Usuario
from app.modules.membresias.models import Membresia
from app.modules.notificaciones import service as notificaciones_service
from app.modules.sedes.models import Sede


def tiene_membresia_activa(db: Session, socio_id: uuid.UUID) -> bool:
    return (
        db.query(Membresia)
        .filter(Membresia.socio_id == socio_id, Membresia.estado == "activa")
        .first()
        is not None
    )


def esta_dentro(db: Session, socio_id: uuid.UUID, sede_id: uuid.UUID) -> bool:
    ultimo = (
        db.query(Acceso)
        .filter(Acceso.socio_id == socio_id, Acceso.sede_id == sede_id)
        .order_by(Acceso.fecha_hora.desc())
        .first()
    )
    return ultimo is not None and ultimo.tipo == "entrada"


def _buscar_reserva_en_curso(db: Session, socio_id: uuid.UUID, ahora: datetime) -> Reserva | None:
    candidatas = (
        db.query(Reserva, Clase)
        .join(Clase, Reserva.clase_id == Clase.id)
        .filter(
            Reserva.socio_id == socio_id,
            Reserva.estado == "confirmada",
            Clase.estado == "activa",
            Clase.fecha_hora <= ahora,
        )
        .all()
    )
    for reserva, clase in candidatas:
        if ahora <= clase.fecha_hora + timedelta(minutes=clase.duracion_minutos):
            return reserva
    return None


def _marcar_asistencia_si_aplica(db: Session, socio_id: uuid.UUID) -> None:
    ahora = datetime.utcnow()
    reserva = _buscar_reserva_en_curso(db, socio_id, ahora)
    if reserva is None:
        return

    ya_registrada = db.query(Asistencia).filter(Asistencia.reserva_id == reserva.id).first()
    if ya_registrada is not None:
        return

    clases_service.checkin_asistencia(db, reserva)


def registrar_checkin(db: Session, socio_id: uuid.UUID, sede_id: uuid.UUID) -> Acceso:
    if not tiene_membresia_activa(db, socio_id):
        raise ValueError("Membresía congelada, cancelada o inexistente: no se permite el acceso")

    # Lock consultivo (advisory lock) por socio: como el primer check-in del
    # día no tiene una fila previa de `accesos` que bloquear con FOR UPDATE,
    # se serializa por socio_id a nivel de BD para que dos check-ins
    # concurrentes del mismo socio no lean el mismo "último acceso" y
    # generen dos entradas/salidas seguidas. Se libera al terminar la
    # transacción (commit/rollback).
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:socio_id))"), {"socio_id": str(socio_id)})

    tipo = "salida" if esta_dentro(db, socio_id, sede_id) else "entrada"
    acceso = Acceso(socio_id=socio_id, sede_id=sede_id, tipo=tipo)
    db.add(acceso)

    if tipo == "entrada":
        _marcar_asistencia_si_aplica(db, socio_id)

    db.commit()
    db.refresh(acceso)

    if tipo == "entrada":
        _avisar_si_aforo_superado(db, sede_id)

    return acceso


def _avisar_si_aforo_superado(db: Session, sede_id: uuid.UUID) -> None:
    sede = db.get(Sede, sede_id)
    info = calcular_aforo_actual(db, sede)
    if not info["aforo_superado"]:
        return

    gestores = db.query(Usuario).filter(Usuario.rol == "gestor_sede", Usuario.sede_id == sede_id).all()
    for gestor in gestores:
        notificaciones_service.encolar_notificacion(
            db,
            gestor.id,
            "aforo_superado",
            sede_nombre=sede.nombre,
            ocupacion_actual=str(info["ocupacion_actual"]),
            aforo_maximo=str(info["aforo_maximo"]),
        )


def calcular_aforo_actual(db: Session, sede: Sede) -> dict:
    subq = (
        db.query(Acceso.socio_id, func.max(Acceso.fecha_hora).label("ultima"))
        .filter(Acceso.sede_id == sede.id)
        .group_by(Acceso.socio_id)
        .subquery()
    )
    ocupacion_actual = (
        db.query(func.count())
        .select_from(Acceso)
        .join(
            subq,
            (Acceso.socio_id == subq.c.socio_id) & (Acceso.fecha_hora == subq.c.ultima),
        )
        .filter(Acceso.sede_id == sede.id, Acceso.tipo == "entrada")
        .scalar()
    )

    return {
        "sede_id": sede.id,
        "ocupacion_actual": ocupacion_actual,
        "aforo_maximo": sede.aforo_maximo,
        # Criterio de aceptación (spec.md): superar el aforo no bloquea el
        # check-in, solo se informa aquí para que gestor_sede decida
        # manualmente. El aviso proactivo queda pendiente del módulo 011
        # (Notificaciones), igual que el resto de eventos ya documentados
        # en clases/service.py y pagos/service.py.
        "aforo_superado": ocupacion_actual > sede.aforo_maximo,
    }
