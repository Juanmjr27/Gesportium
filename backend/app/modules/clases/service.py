import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.clases.models import Asistencia, Clase, Reserva
from app.modules.notificaciones import service as notificaciones_service
from app.modules.socios.models import Socio

# Tiempo mínimo antes del inicio de la clase para cancelar sin que quede
# marcada como "fuera de plazo" (spec.md: parametrizable; sin UI de
# configuración todavía, se fija aquí como constante).
VENTANA_CANCELACION_MINUTOS = 120

# Horas mínimas de antelación para poder cancelar una reserva CONFIRMADA
# (specs/005). No aplica a salir de la lista de espera, que no ocupa plaza
# y puede abandonarse en cualquier momento. Pensada para hacerse
# configurable desde el módulo 014 más adelante; de momento es constante.
HORAS_LIMITE_CANCELACION_CONFIRMADA = 1


def contar_confirmadas(db: Session, clase_id: uuid.UUID) -> int:
    return db.query(Reserva).filter(Reserva.clase_id == clase_id, Reserva.estado == "confirmada").count()


def contar_lista_espera(db: Session, clase_id: uuid.UUID) -> int:
    return db.query(Reserva).filter(Reserva.clase_id == clase_id, Reserva.estado == "lista_espera").count()


def calcular_ocupacion(db: Session, clase: Clase) -> dict:
    confirmadas = contar_confirmadas(db, clase.id)
    return {
        "confirmadas": confirmadas,
        "plazas_disponibles": max(clase.aforo_maximo - confirmadas, 0),
        "en_lista_espera": contar_lista_espera(db, clase.id),
    }


def crear_clase(db: Session, **datos) -> Clase:
    clase = Clase(**datos, estado="activa")
    db.add(clase)
    db.commit()
    db.refresh(clase)
    return clase


def reservar_clase(db: Session, clase: Clase, socio_id: uuid.UUID) -> Reserva:
    # Bloquea la fila de la clase para serializar reservas concurrentes:
    # sin este lock, dos peticiones simultáneas para la última plaza pueden
    # leer la misma cuenta de "confirmadas" antes de que ninguna inserte,
    # provocando overbooking. El lock se libera al hacer commit/rollback.
    db.query(Clase).filter(Clase.id == clase.id).with_for_update().one()

    confirmadas = contar_confirmadas(db, clase.id)
    estado = "confirmada" if confirmadas < clase.aforo_maximo else "lista_espera"

    reserva = Reserva(clase_id=clase.id, socio_id=socio_id, estado=estado)
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return reserva


def _promocionar_lista_espera(db: Session, clase_id: uuid.UUID, clase: Clase) -> Reserva | None:
    siguiente = (
        db.query(Reserva)
        .filter(Reserva.clase_id == clase_id, Reserva.estado == "lista_espera")
        .order_by(Reserva.fecha_reserva.asc())
        .first()
    )
    if siguiente is None:
        return None

    siguiente.estado = "confirmada"
    socio = db.get(Socio, siguiente.socio_id)
    notificaciones_service.encolar_notificacion(
        db,
        socio.usuario_id,
        "plaza_liberada",
        clase_nombre=clase.nombre,
        clase_fecha=clase.fecha_hora.isoformat(),
    )
    return siguiente


def cancelar_reserva(db: Session, reserva: Reserva, clase: Clase) -> Reserva:
    ahora = datetime.utcnow()
    estaba_confirmada = reserva.estado == "confirmada"

    reserva.estado = "cancelada"
    reserva.fecha_cancelacion = ahora
    reserva.cancelada_fuera_plazo = ahora > clase.fecha_hora - timedelta(minutes=VENTANA_CANCELACION_MINUTOS)

    if estaba_confirmada:
        _promocionar_lista_espera(db, clase.id, clase)

    db.commit()
    db.refresh(reserva)
    return reserva


def checkin_asistencia(db: Session, reserva: Reserva) -> Asistencia:
    asistencia = Asistencia(reserva_id=reserva.id, fecha_checkin=datetime.utcnow())
    db.add(asistencia)
    db.commit()
    db.refresh(asistencia)
    return asistencia


def listar_clases_futuras_activas(db: Session, entrenador_id: uuid.UUID) -> list[Clase]:
    return (
        db.query(Clase)
        .filter(
            Clase.entrenador_id == entrenador_id,
            Clase.estado == "activa",
            Clase.fecha_hora > datetime.utcnow(),
        )
        .all()
    )


def reasignar_por_baja_entrenador(
    db: Session,
    entrenador_id: uuid.UUID,
    decision: str,
    nuevo_entrenador_id: uuid.UUID | None,
) -> list[Clase]:
    clases_futuras = listar_clases_futuras_activas(db, entrenador_id)
    tipo_evento = "clase_reasignada" if decision == "reasignar" else "clase_cancelada"

    for clase in clases_futuras:
        if decision == "reasignar":
            clase.entrenador_id = nuevo_entrenador_id
        else:
            clase.estado = "cancelada"

        reservas_confirmadas = (
            db.query(Reserva).filter(Reserva.clase_id == clase.id, Reserva.estado == "confirmada").all()
        )
        for reserva in reservas_confirmadas:
            socio = db.get(Socio, reserva.socio_id)
            notificaciones_service.encolar_notificacion(
                db,
                socio.usuario_id,
                tipo_evento,
                clase_nombre=clase.nombre,
                clase_fecha=clase.fecha_hora.isoformat(),
            )

    db.commit()
    for clase in clases_futuras:
        db.refresh(clase)
    return clases_futuras
