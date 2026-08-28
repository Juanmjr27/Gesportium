import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.membresias import service as membresias_service
from app.modules.membresias.models import Membresia, PlanMembresia
from app.modules.notificaciones import service as notificaciones_service
from app.modules.pagos.models import Factura, HistorialAccionPago, Pago, Remesa, RemesaPago
from app.modules.pagos.pdf import generar_pdf_factura
from app.modules.socios.models import Socio

# Reintentos permitidos antes de considerar el pago definitivamente fallido
# y congelar la membresía (spec.md: "N reintentos", parametrizable).
MAX_REINTENTOS = 3


def hay_pago_pendiente(db: Session, membresia_id: uuid.UUID) -> bool:
    return db.query(Pago).filter(Pago.membresia_id == membresia_id, Pago.estado == "pendiente").first() is not None


def _registrar_auditoria(db: Session, entidad_tipo: str, entidad_id: uuid.UUID, accion: str, autor_id: uuid.UUID) -> None:
    db.add(
        HistorialAccionPago(
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            accion=accion,
            autor_id=autor_id,
        )
    )


def _siguiente_numero_factura(db: Session) -> str:
    """Unicidad garantizada a nivel de BD vía SEQUENCE de Postgres
    (`factura_numero_seq`, migración 9f3b6d2a1c47): nextval() es atómico y
    no transaccional, así que dos transacciones concurrentes (o dos tests
    aislados por SAVEPOINT) nunca obtienen el mismo secuencial — a
    diferencia de contar filas de `facturas` dentro de la propia
    transacción, que sí colisionaba (specs/008 T11, confirmado en
    specs/018 T5).
    """
    secuencial = db.execute(text("SELECT nextval('factura_numero_seq')")).scalar()
    return f"F-{date.today().year}-{secuencial:06d}"


def generar_factura(db: Session, pago: Pago, autor_id: uuid.UUID | None = None) -> Factura:
    autor_id = autor_id or membresias_service.obtener_o_crear_usuario_sistema(db).id
    numero = _siguiente_numero_factura(db)
    pdf_url = generar_pdf_factura(numero, pago)

    factura = Factura(pago_id=pago.id, numero=numero, pdf_url=pdf_url)
    db.add(factura)
    db.flush()
    _registrar_auditoria(db, "factura", factura.id, "emitida", autor_id)
    db.commit()
    db.refresh(factura)
    return factura


def anular_factura(db: Session, factura: Factura, autor_id: uuid.UUID) -> Factura:
    if factura.anulada:
        raise ValueError("La factura ya está anulada")

    factura.anulada = True
    _registrar_auditoria(db, "factura", factura.id, "anulada", autor_id)
    db.commit()
    db.refresh(factura)
    return factura


def reemitir_factura(db: Session, factura: Factura, autor_id: uuid.UUID) -> Factura:
    """No se edita la factura anulada (spec.md: "no se editan, solo se
    anulan y reemiten"): se genera una Factura nueva para el mismo pago,
    con número y PDF propios; la anulada permanece intacta como registro.
    """
    if not factura.anulada:
        raise ValueError("Solo se puede reemitir una factura anulada")

    pago = db.get(Pago, factura.pago_id)
    nueva_factura = generar_factura(db, pago, autor_id=autor_id)
    _registrar_auditoria(db, "factura", nueva_factura.id, "reemitida", autor_id)
    db.commit()
    db.refresh(nueva_factura)
    return nueva_factura


def generar_cobro_pendiente(db: Session, membresia: Membresia, plan: PlanMembresia) -> Pago:
    ya_facturado = (
        db.query(Pago)
        .filter(Pago.membresia_id == membresia.id, Pago.periodo == membresia.fecha_proxima_renovacion)
        .first()
    )
    if ya_facturado is not None:
        raise ValueError("Ya existe un cobro generado para este periodo de la membresía")

    pago = Pago(
        socio_id=membresia.socio_id,
        membresia_id=membresia.id,
        concepto=f"Renovación membresía ({plan.nombre})",
        importe=plan.precio,
        estado="pendiente",
        periodo=membresia.fecha_proxima_renovacion,
    )
    db.add(pago)
    db.flush()
    autor_id = membresias_service.obtener_o_crear_usuario_sistema(db).id
    _registrar_auditoria(db, "pago", pago.id, "generado", autor_id)
    db.commit()
    db.refresh(pago)
    return pago


def _emitir_evento_pago_fallido(db: Session, pago: Pago) -> None:
    socio = db.get(Socio, pago.socio_id)
    notificaciones_service.encolar_notificacion(
        db,
        socio.usuario_id,
        "pago_fallido",
        importe=str(pago.importe),
        concepto=pago.concepto,
    )


def intentar_cobro(db: Session, pago: Pago, exitoso: bool) -> Pago:
    """Registra un intento de cobro contra la pasarela simulada (spec.md:
    "pasarela de pago simulada, no real"). El resultado (`exitoso`) lo
    decide el llamador — en producción sería la respuesta de la pasarela;
    aquí no hay integración real que consultar.
    """
    if pago.estado != "pendiente":
        raise ValueError("Solo se puede reintentar un pago pendiente")

    autor_id = membresias_service.obtener_o_crear_usuario_sistema(db).id

    if exitoso:
        pago.estado = "exitoso"
        _registrar_auditoria(db, "pago", pago.id, "cobro_exitoso", autor_id)
        db.commit()
        db.refresh(pago)
        generar_factura(db, pago, autor_id=autor_id)
        return pago

    pago.intentos += 1
    if pago.intentos >= MAX_REINTENTOS:
        pago.estado = "fallido"
        _registrar_auditoria(db, "pago", pago.id, "cobro_fallido", autor_id)
        db.commit()
        db.refresh(pago)

        # Único mecanismo autorizado para congelar por impago (plan.md Fase
        # 2): nunca se escribe directamente en las tablas del módulo 004.
        if pago.membresia_id is not None:
            membresia = db.get(Membresia, pago.membresia_id)
            if membresia is not None and membresia.estado == "activa":
                membresias_service.congelar_por_impago(db, membresia)

        _emitir_evento_pago_fallido(db, pago)
    else:
        _registrar_auditoria(db, "pago", pago.id, "reintento_fallido", autor_id)
        db.commit()
        db.refresh(pago)

    return pago


def procesar_cobros_automaticos(db: Session, resultados_pasarela: dict[uuid.UUID, bool] | None = None) -> list[Pago]:
    """Job interno de cobro automático (plan.md Fase 2: "endpoint de cobro
    automático no expuesto públicamente (job interno)"). No se expone vía
    router por el mismo motivo que membresias.service.ejecutar_job_renovacion
    tampoco lo hace: no existe infraestructura de auth de servicio, y el rol
    "sistema" no puede autenticarse (ver membresias/service.py).

    Recorre las membresías próximas a vencer con renovación automática
    (ejecutar_job_renovacion ya excluye las congeladas) y genera/reintenta
    su cobro. `resultados_pasarela` permite inyectar el resultado simulado
    por membresia_id (usado en tests); si no se indica, se asume éxito.
    """
    resultados_pasarela = resultados_pasarela or {}
    pagos: list[Pago] = []

    for membresia in membresias_service.ejecutar_job_renovacion(db):
        plan = db.get(PlanMembresia, membresia.plan_id)

        pago = (
            db.query(Pago)
            .filter(Pago.membresia_id == membresia.id, Pago.periodo == membresia.fecha_proxima_renovacion)
            .first()
        )
        if pago is None:
            pago = generar_cobro_pendiente(db, membresia, plan)

        if pago.estado != "pendiente":
            continue

        exitoso = resultados_pasarela.get(membresia.id, True)
        pagos.append(intentar_cobro(db, pago, exitoso))

    return pagos


def generar_remesa(db: Session, sede_id: uuid.UUID, fecha: date, autor_id: uuid.UUID | None = None) -> Remesa:
    autor_id = autor_id or membresias_service.obtener_o_crear_usuario_sistema(db).id

    pagos = (
        db.query(Pago)
        .join(Socio, Socio.id == Pago.socio_id)
        .filter(
            Socio.sede_id == sede_id,
            Pago.estado == "exitoso",
            Pago.fecha >= datetime.combine(fecha, datetime.min.time()),
            Pago.fecha < datetime.combine(fecha, datetime.max.time()),
            ~Pago.id.in_(db.query(RemesaPago.pago_id)),
        )
        .all()
    )

    total = sum((p.importe for p in pagos), Decimal("0"))
    remesa = Remesa(sede_id=sede_id, fecha=fecha, total=total)
    db.add(remesa)
    db.flush()

    for pago in pagos:
        db.add(RemesaPago(remesa_id=remesa.id, pago_id=pago.id))

    # Cubre también las filas de RemesaPago creadas en esta misma operación:
    # se generan atómicamente junto con la remesa, así que auditar la
    # remesa ya identifica quién generó ambas.
    _registrar_auditoria(db, "remesa", remesa.id, "generada", autor_id)

    db.commit()
    db.refresh(remesa)
    return remesa
