import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.notificaciones import plantillas
from app.modules.notificaciones.models import Notificacion, PreferenciaNotificacion

# Reintentos permitidos antes de dar la notificación por fallida
# definitivamente (mismo umbral y patrón que pagos.service.MAX_REINTENTOS).
MAX_REINTENTOS = 3


def obtener_preferencia(db: Session, usuario_id: uuid.UUID) -> PreferenciaNotificacion:
    preferencia = db.get(PreferenciaNotificacion, usuario_id)
    if preferencia is not None:
        return preferencia

    preferencia = PreferenciaNotificacion(usuario_id=usuario_id, marketing_activo=True)
    db.add(preferencia)
    db.flush()
    return preferencia


def actualizar_preferencia(db: Session, usuario_id: uuid.UUID, marketing_activo: bool) -> PreferenciaNotificacion:
    preferencia = obtener_preferencia(db, usuario_id)
    preferencia.marketing_activo = marketing_activo
    db.commit()
    db.refresh(preferencia)
    return preferencia


def encolar_notificacion(
    db: Session,
    usuario_id: uuid.UUID,
    tipo: str,
    canal: str = "email",
    **contexto: str,
) -> Notificacion | None:
    """Servicio interno reutilizable por otros módulos (tasks.md T4). Un
    fallo aquí nunca debe propagarse a quien la llama (spec.md: "un fallo de
    envío no bloquea la acción que lo disparó") — pero encolar es solo una
    escritura local, no un envío, así que no hace falta capturar excepciones:
    si falla, debe fallar la operación completa igual que cualquier otro
    db.add() del resto del código.

    Devuelve None sin encolar si es de tipo "marketing" y el usuario lo ha
    desactivado (spec.md: "transaccionales no se pueden desactivar" implica
    que solo "marketing" está sujeto a esta preferencia).
    """
    if tipo == "marketing" and not obtener_preferencia(db, usuario_id).marketing_activo:
        return None

    asunto, cuerpo = plantillas.renderizar(tipo, **contexto)

    notificacion = Notificacion(
        usuario_id=usuario_id,
        tipo=tipo,
        canal=canal,
        asunto=asunto,
        cuerpo=cuerpo,
    )
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def _procesar_envio(db: Session, notificacion: Notificacion, exitoso: bool) -> Notificacion:
    if exitoso:
        notificacion.estado = "enviada"
        notificacion.fecha_envio = datetime.utcnow()
    else:
        notificacion.intentos += 1
        if notificacion.intentos >= MAX_REINTENTOS:
            notificacion.estado = "fallida"

    db.commit()
    db.refresh(notificacion)
    return notificacion


def procesar_cola_notificaciones(
    db: Session, resultados_envio: dict[uuid.UUID, bool] | None = None
) -> list[Notificacion]:
    """Worker/job de envío con reintentos (tasks.md T5). No existe en este
    proyecto infraestructura SMTP real configurada (fastapi-mail queda
    declarado en plan.md Fase 4 como dependencia lista para conectar
    credenciales, igual que quedó pendiente en identidad/router.py); se
    simula el resultado del envío igual que pagos.service.procesar_cobros_automaticos
    simula la pasarela de pago. `resultados_envio` permite inyectar el
    resultado por notificacion_id (usado en tests); por defecto se asume éxito.
    """
    resultados_envio = resultados_envio or {}
    pendientes = db.query(Notificacion).filter(Notificacion.estado == "pendiente").all()

    for notificacion in pendientes:
        exitoso = resultados_envio.get(notificacion.id, True)
        _procesar_envio(db, notificacion, exitoso)

    return pendientes
