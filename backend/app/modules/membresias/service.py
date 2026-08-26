import calendar
import uuid
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.modules.identidad.models import Usuario
from app.modules.membresias.models import (
    CongelacionMembresia,
    HistorialEstadosMembresia,
    Membresia,
    PlanMembresia,
)
from app.modules.notificaciones import service as notificaciones_service
from app.modules.socios import service as socios_service

DIAS_UMBRAL_PROXIMA_A_VENCER = 3

MESES_POR_DURACION = {"mensual": 1, "trimestral": 3, "anual": 12}

USUARIO_SISTEMA_EMAIL = "sistema@gesportium.internal"


def _sumar_meses(fecha: date, meses: int) -> date:
    mes_total = fecha.month - 1 + meses
    anio = fecha.year + mes_total // 12
    mes = mes_total % 12 + 1
    dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia)


def calcular_proxima_renovacion(fecha_inicio: date, duracion: str) -> date:
    return _sumar_meses(fecha_inicio, MESES_POR_DURACION[duracion])


def obtener_o_crear_usuario_sistema(db: Session) -> Usuario:
    """Cuenta técnica usada como autor_id cuando el cambio de estado lo dispara
    un proceso interno (job de renovación, o el módulo 008 vía congelar_por_impago).
    No tiene rol reconocido por require_roles, por lo que no puede autenticarse ni
    acceder a ningún endpoint — solo existe para satisfacer la FK de auditoría.
    """
    usuario = db.query(Usuario).filter(Usuario.email == USUARIO_SISTEMA_EMAIL).first()
    if usuario is not None:
        return usuario

    usuario = Usuario(
        email=USUARIO_SISTEMA_EMAIL,
        password_hash=uuid.uuid4().hex,
        rol="sistema",
        sede_id=None,
        activo=True,
    )
    db.add(usuario)
    db.flush()
    return usuario


def _registrar_historial(db: Session, membresia: Membresia, estado_anterior: str | None, autor_id: uuid.UUID) -> None:
    db.add(
        HistorialEstadosMembresia(
            membresia_id=membresia.id,
            estado_anterior=estado_anterior,
            estado_nuevo=membresia.estado,
            autor_id=autor_id,
        )
    )


def crear_membresia(db: Session, socio_id: uuid.UUID, plan: PlanMembresia, fecha_inicio: date, renovacion_automatica: bool, autor_id: uuid.UUID) -> Membresia:
    membresia = Membresia(
        socio_id=socio_id,
        plan_id=plan.id,
        fecha_inicio=fecha_inicio,
        fecha_proxima_renovacion=calcular_proxima_renovacion(fecha_inicio, plan.duracion),
        renovacion_automatica=renovacion_automatica,
        estado="activa",
    )
    db.add(membresia)
    db.flush()
    _registrar_historial(db, membresia, estado_anterior=None, autor_id=autor_id)
    db.commit()
    db.refresh(membresia)
    return membresia


def congelar_membresia(db: Session, membresia: Membresia, origen: str, autor_id: uuid.UUID, motivo: str | None = None) -> Membresia:
    estado_anterior = membresia.estado
    db.add(
        CongelacionMembresia(
            membresia_id=membresia.id,
            fecha_inicio=date.today(),
            fecha_fin=None,
            motivo=motivo,
            origen=origen,
        )
    )
    membresia.estado = "congelada"
    _registrar_historial(db, membresia, estado_anterior, autor_id)
    db.commit()
    db.refresh(membresia)
    return membresia


def congelar_por_impago(db: Session, membresia: Membresia) -> Membresia:
    """Contrato interno para el módulo 008: única vía autorizada para que el
    job de cobro (pagos/service.py intentar_cobro) congele una membresía
    tras agotar reintentos. No expuesta como endpoint HTTP con auth de
    servicio (esa infraestructura no existe); se invoca como llamada de
    servicio directa, igual que el resto de contratos internos entre
    módulos de este proyecto (ver clases/service.py, entrenadores/service.py).
    """
    usuario_sistema = obtener_o_crear_usuario_sistema(db)
    return congelar_membresia(db, membresia, origen="impago", autor_id=usuario_sistema.id, motivo="Impago tras reintentos agotados")


def hay_pagos_pendientes(db: Session, membresia_id: uuid.UUID) -> bool:
    """Contrato con el módulo 008 (Pagos y facturación): un pago queda en
    estado 'pendiente' mientras se están agotando sus reintentos (ver
    pagos/service.py intentar_cobro). Mientras exista uno así para esta
    membresía, se considera que hay un cobro sin resolver.
    """
    from app.modules.pagos import service as pagos_service

    return pagos_service.hay_pago_pendiente(db, membresia_id)


def reactivar_membresia(db: Session, membresia: Membresia, autor_id: uuid.UUID) -> Membresia:
    congelacion_activa = (
        db.query(CongelacionMembresia)
        .filter(CongelacionMembresia.membresia_id == membresia.id, CongelacionMembresia.fecha_fin.is_(None))
        .order_by(CongelacionMembresia.fecha_inicio.desc())
        .first()
    )

    if congelacion_activa is not None and congelacion_activa.origen == "impago" and hay_pagos_pendientes(db, membresia.id):
        raise ValueError("No se puede reactivar: hay pagos pendientes asociados a la congelación por impago")

    if congelacion_activa is not None:
        congelacion_activa.fecha_fin = date.today()

    estado_anterior = membresia.estado
    membresia.estado = "activa"
    _registrar_historial(db, membresia, estado_anterior, autor_id)
    db.commit()
    db.refresh(membresia)
    return membresia


def cancelar_membresia(db: Session, membresia: Membresia, plan: PlanMembresia, autor_id: uuid.UUID) -> Membresia:
    if hay_pagos_pendientes(db, membresia.id):
        raise ValueError("No se puede cancelar: hay pagos pendientes sin resolver")

    estado_anterior = membresia.estado
    membresia.estado = "cancelada"
    membresia.fecha_cancelacion = date.today() + timedelta(days=plan.preaviso_cancelacion_dias)
    _registrar_historial(db, membresia, estado_anterior, autor_id)
    db.commit()
    db.refresh(membresia)
    return membresia


def ejecutar_job_renovacion(db: Session) -> list[Membresia]:
    """Recorre membresías activas con renovación automática, omite las
    congeladas y devuelve las que están a <= DIAS_UMBRAL_PROXIMA_A_VENCER
    días de su fecha_proxima_renovacion. Encola el aviso "próxima a vencer"
    (módulo 011) para cada una.
    """
    limite = date.today() + timedelta(days=DIAS_UMBRAL_PROXIMA_A_VENCER)
    membresias = (
        db.query(Membresia)
        .filter(
            Membresia.estado == "activa",
            Membresia.renovacion_automatica.is_(True),
            Membresia.fecha_proxima_renovacion <= limite,
        )
        .all()
    )

    for membresia in membresias:
        socio = socios_service.obtener_socio(db, membresia.socio_id)
        notificaciones_service.encolar_notificacion(
            db,
            socio.usuario_id,
            "membresia_proxima_vencer",
            fecha_renovacion=membresia.fecha_proxima_renovacion.isoformat(),
        )

    return membresias


def ejecutar_job_vencimiento(db: Session) -> list[Membresia]:
    """Transiciona a "vencida" las membresías activas SIN renovación
    automática cuya fecha_proxima_renovacion ya pasó. Las que sí tienen
    renovación automática no entran aquí: su desenlace (se quedan activas
    tras un cobro exitoso, o pasan a congeladas por impago) ya lo resuelve
    pagos.service.procesar_cobros_automaticos vía ejecutar_job_renovacion;
    "vencida" cubre el caso en que nunca iba a intentarse ningún cobro.

    Job interno (mismo patrón que ejecutar_job_renovacion): no expuesto
    como endpoint HTTP, pensado para invocarse desde un scheduler externo.
    """
    membresias = (
        db.query(Membresia)
        .filter(
            Membresia.estado == "activa",
            Membresia.renovacion_automatica.is_(False),
            Membresia.fecha_proxima_renovacion < date.today(),
        )
        .all()
    )

    autor_id = obtener_o_crear_usuario_sistema(db).id
    for membresia in membresias:
        estado_anterior = membresia.estado
        membresia.estado = "vencida"
        _registrar_historial(db, membresia, estado_anterior, autor_id)

        socio = socios_service.obtener_socio(db, membresia.socio_id)
        notificaciones_service.encolar_notificacion(
            db,
            socio.usuario_id,
            "membresia_vencida",
            fecha_vencimiento=membresia.fecha_proxima_renovacion.isoformat(),
        )

    db.commit()
    for membresia in membresias:
        db.refresh(membresia)
    return membresias
