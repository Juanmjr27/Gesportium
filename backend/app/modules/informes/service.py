import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.modules.clases.models import Clase, Reserva
from app.modules.crm.models import Lead
from app.modules.identidad.models import Usuario
from app.modules.pagos.models import Pago
from app.modules.socios.models import HistorialAccionSocio, Socio


def _rango_datetime(fecha_inicio: date, fecha_fin: date) -> tuple[datetime, datetime]:
    inicio = datetime.combine(fecha_inicio, time.min)
    fin = datetime.combine(fecha_fin + timedelta(days=1), time.min)
    return inicio, fin


def informe_socios(db: Session, sede_id: uuid.UUID | None, fecha_inicio: date, fecha_fin: date) -> dict:
    inicio, fin = _rango_datetime(fecha_inicio, fecha_fin)

    query = (
        db.query(HistorialAccionSocio, Usuario.email)
        .join(Socio, Socio.id == HistorialAccionSocio.socio_id)
        .join(Usuario, Usuario.id == Socio.usuario_id)
        .filter(HistorialAccionSocio.fecha >= inicio, HistorialAccionSocio.fecha < fin)
    )
    if sede_id is not None:
        query = query.filter(Socio.sede_id == sede_id)

    detalle = []
    total_altas = 0
    total_bajas = 0
    for accion, email in query.order_by(HistorialAccionSocio.fecha).all():
        detalle.append(
            {"socio_id": accion.socio_id, "email": email, "accion": accion.accion, "fecha": accion.fecha}
        )
        if accion.accion == "alta":
            total_altas += 1
        elif accion.accion == "baja":
            total_bajas += 1

    activos_query = db.query(Socio).filter(Socio.activo.is_(True))
    if sede_id is not None:
        activos_query = activos_query.filter(Socio.sede_id == sede_id)

    return {
        "sede_id": sede_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_altas": total_altas,
        "total_bajas": total_bajas,
        "socios_activos_al_cierre": activos_query.count(),
        "detalle": detalle,
    }


def informe_financiero(db: Session, sede_id: uuid.UUID | None, fecha_inicio: date, fecha_fin: date) -> dict:
    inicio, fin = _rango_datetime(fecha_inicio, fecha_fin)

    query = (
        db.query(Pago, Usuario.email)
        .join(Socio, Socio.id == Pago.socio_id)
        .join(Usuario, Usuario.id == Socio.usuario_id)
        .filter(Pago.fecha >= inicio, Pago.fecha < fin)
    )
    if sede_id is not None:
        query = query.filter(Socio.sede_id == sede_id)

    detalle = []
    total_ingresos = 0.0
    total_impagos = 0.0
    for pago, email in query.order_by(Pago.fecha).all():
        detalle.append(
            {
                "pago_id": pago.id,
                "socio_id": pago.socio_id,
                "email": email,
                "concepto": pago.concepto,
                "importe": float(pago.importe),
                "estado": pago.estado,
                "fecha": pago.fecha,
            }
        )
        if pago.estado == "exitoso":
            total_ingresos += float(pago.importe)
        elif pago.estado == "fallido":
            total_impagos += float(pago.importe)

    return {
        "sede_id": sede_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_ingresos": round(total_ingresos, 2),
        "total_impagos": round(total_impagos, 2),
        "detalle": detalle,
    }


def informe_ocupacion(db: Session, sede_id: uuid.UUID | None, fecha_inicio: date, fecha_fin: date) -> dict:
    inicio, fin = _rango_datetime(fecha_inicio, fecha_fin)

    query = db.query(Clase).filter(Clase.fecha_hora >= inicio, Clase.fecha_hora < fin)
    if sede_id is not None:
        query = query.filter(Clase.sede_id == sede_id)

    detalle = []
    ratios = []
    for clase in query.order_by(Clase.fecha_hora).all():
        confirmadas = (
            db.query(Reserva).filter(Reserva.clase_id == clase.id, Reserva.estado == "confirmada").count()
        )
        ocupacion_pct = round(confirmadas / clase.aforo_maximo * 100, 2)
        ratios.append(ocupacion_pct)
        detalle.append(
            {
                "clase_id": clase.id,
                "nombre": clase.nombre,
                "fecha_hora": clase.fecha_hora,
                "aforo_maximo": clase.aforo_maximo,
                "reservas_confirmadas": confirmadas,
                "ocupacion_pct": ocupacion_pct,
            }
        )

    return {
        "sede_id": sede_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "ocupacion_media_pct": round(sum(ratios) / len(ratios), 2) if ratios else 0.0,
        "detalle": detalle,
    }


def informe_comercial(db: Session, sede_id: uuid.UUID | None, fecha_inicio: date, fecha_fin: date) -> dict:
    inicio, fin = _rango_datetime(fecha_inicio, fecha_fin)

    query = db.query(Lead).filter(Lead.fecha_creacion >= inicio, Lead.fecha_creacion < fin)
    if sede_id is not None:
        query = query.filter(Lead.sede_interes_id == sede_id)

    leads = query.order_by(Lead.fecha_creacion).all()
    convertidos = sum(1 for lead in leads if lead.estado == "convertido")
    detalle = [
        {
            "lead_id": lead.id,
            "nombre": lead.nombre,
            "origen": lead.origen,
            "estado": lead.estado,
            "fecha_creacion": lead.fecha_creacion,
        }
        for lead in leads
    ]

    return {
        "sede_id": sede_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_leads": len(leads),
        "convertidos": convertidos,
        "tasa_conversion_pct": round(convertidos / len(leads) * 100, 2) if leads else 0.0,
        "detalle": detalle,
    }


GENERADORES_INFORME = {
    "socios": informe_socios,
    "financiero": informe_financiero,
    "ocupacion": informe_ocupacion,
    "comercial": informe_comercial,
}


def calcular_informe(tipo: str, db: Session, sede_id: uuid.UUID | None, fecha_inicio: date, fecha_fin: date) -> dict:
    generador = GENERADORES_INFORME.get(tipo)
    if generador is None:
        raise ValueError(f"Tipo de informe desconocido: {tipo}")
    return generador(db, sede_id, fecha_inicio, fecha_fin)
