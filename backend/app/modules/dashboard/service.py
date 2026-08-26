import uuid
from datetime import date

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.modules.clases.models import Clase, Reserva
from app.modules.crm.models import Lead
from app.modules.pagos.models import Pago
from app.modules.socios.models import HistorialAccionSocio, Socio


def _primer_dia_mes(fecha: date) -> date:
    return fecha.replace(day=1)


def _primer_dia_mes_siguiente(fecha: date) -> date:
    primer_dia = _primer_dia_mes(fecha)
    if primer_dia.month == 12:
        return date(primer_dia.year + 1, 1, 1)
    return date(primer_dia.year, primer_dia.month + 1, 1)


def _primer_dia_mes_anterior(fecha: date) -> date:
    primer_dia = _primer_dia_mes(fecha)
    if primer_dia.month == 1:
        return date(primer_dia.year - 1, 12, 1)
    return date(primer_dia.year, primer_dia.month - 1, 1)


def _variacion_pct(actual: float, anterior: float) -> float | None:
    if anterior == 0:
        return None
    return round((actual - anterior) / anterior * 100, 2)


def _comparativa(actual: float, anterior: float) -> dict:
    return {"valor": actual, "valor_periodo_anterior": anterior, "variacion_pct": _variacion_pct(actual, anterior)}


def _contar_socios_activos(db: Session, sede_id: uuid.UUID | None) -> int:
    query = db.query(func.count(Socio.id)).filter(Socio.activo.is_(True))
    if sede_id is not None:
        query = query.filter(Socio.sede_id == sede_id)
    return query.scalar() or 0


def _contar_socios_activos_a_fecha(db: Session, sede_id: uuid.UUID | None, fecha_corte: date) -> int:
    """Reconstruye el nº de socios activos a una fecha pasada a partir de
    fecha_alta/fecha_baja (003), para poder comparar contra el snapshot
    "en vivo" de _contar_socios_activos sin necesitar una tabla de histórico.
    """
    query = db.query(func.count(Socio.id)).filter(
        Socio.fecha_alta < fecha_corte,
        or_(Socio.fecha_baja.is_(None), Socio.fecha_baja >= fecha_corte),
    )
    if sede_id is not None:
        query = query.filter(Socio.sede_id == sede_id)
    return query.scalar() or 0


def _contar_acciones_socio(db: Session, sede_id: uuid.UUID | None, accion: str, inicio: date, fin: date) -> int:
    query = (
        db.query(func.count(HistorialAccionSocio.id))
        .join(Socio, Socio.id == HistorialAccionSocio.socio_id)
        .filter(
            HistorialAccionSocio.accion == accion,
            HistorialAccionSocio.fecha >= inicio,
            HistorialAccionSocio.fecha < fin,
        )
    )
    if sede_id is not None:
        query = query.filter(Socio.sede_id == sede_id)
    return query.scalar() or 0


def _sumar_ingresos(db: Session, sede_id: uuid.UUID | None, inicio: date, fin: date) -> float:
    query = (
        db.query(func.sum(Pago.importe))
        .join(Socio, Socio.id == Pago.socio_id)
        .filter(Pago.estado == "exitoso", Pago.fecha >= inicio, Pago.fecha < fin)
    )
    if sede_id is not None:
        query = query.filter(Socio.sede_id == sede_id)
    total = query.scalar()
    return float(total) if total is not None else 0.0


def _ocupacion_media_clases(db: Session, sede_id: uuid.UUID | None, inicio: date, fin: date) -> float:
    query = db.query(Clase).filter(Clase.fecha_hora >= inicio, Clase.fecha_hora < fin)
    if sede_id is not None:
        query = query.filter(Clase.sede_id == sede_id)
    clases = query.all()
    if not clases:
        return 0.0

    ratios = []
    for clase in clases:
        confirmadas = (
            db.query(func.count(Reserva.id))
            .filter(Reserva.clase_id == clase.id, Reserva.estado == "confirmada")
            .scalar()
            or 0
        )
        ratios.append(confirmadas / clase.aforo_maximo * 100)
    return round(sum(ratios) / len(ratios), 2)


def _tasa_conversion_leads(db: Session, sede_id: uuid.UUID | None, inicio: date, fin: date) -> float:
    query = db.query(Lead).filter(Lead.fecha_creacion >= inicio, Lead.fecha_creacion < fin)
    if sede_id is not None:
        query = query.filter(Lead.sede_interes_id == sede_id)
    leads = query.all()
    if not leads:
        return 0.0

    convertidos = sum(1 for lead in leads if lead.estado == "convertido")
    return round(convertidos / len(leads) * 100, 2)


def calcular_kpis(db: Session, sede_id: uuid.UUID | None) -> dict:
    """Consulta agregada en vivo (sin caché) sobre las tablas de 003/004/005/
    008/010, calculada en el momento de la petición para cumplir el criterio
    de aceptación de la spec 012 ("no cacheados más de 15 min").
    """
    hoy = date.today()
    inicio_actual = _primer_dia_mes(hoy)
    fin_actual = _primer_dia_mes_siguiente(hoy)
    inicio_anterior = _primer_dia_mes_anterior(hoy)
    fin_anterior = inicio_actual

    return {
        "sede_id": sede_id,
        "socios_activos": _comparativa(
            _contar_socios_activos(db, sede_id),
            _contar_socios_activos_a_fecha(db, sede_id, inicio_actual),
        ),
        "altas_mes": _comparativa(
            _contar_acciones_socio(db, sede_id, "alta", inicio_actual, fin_actual),
            _contar_acciones_socio(db, sede_id, "alta", inicio_anterior, fin_anterior),
        ),
        "bajas_mes": _comparativa(
            _contar_acciones_socio(db, sede_id, "baja", inicio_actual, fin_actual),
            _contar_acciones_socio(db, sede_id, "baja", inicio_anterior, fin_anterior),
        ),
        "ingresos_mes": _comparativa(
            _sumar_ingresos(db, sede_id, inicio_actual, fin_actual),
            _sumar_ingresos(db, sede_id, inicio_anterior, fin_anterior),
        ),
        "ocupacion_media_clases": _comparativa(
            _ocupacion_media_clases(db, sede_id, inicio_actual, fin_actual),
            _ocupacion_media_clases(db, sede_id, inicio_anterior, fin_anterior),
        ),
        "tasa_conversion_leads": _comparativa(
            _tasa_conversion_leads(db, sede_id, inicio_actual, fin_actual),
            _tasa_conversion_leads(db, sede_id, inicio_anterior, fin_anterior),
        ),
    }
