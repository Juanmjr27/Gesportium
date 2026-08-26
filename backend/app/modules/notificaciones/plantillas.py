# Plantillas por tipo de evento (spec.md T7, tasks.md T7). Cada plantilla
# se interpola con `str.format(**contexto)`: el contexto lo aporta cada
# módulo emisor del evento (ver ganchos en accesos/clases/membresias/pagos
# service.py) y debe incluir exactamente las claves usadas aquí.
PLANTILLAS = {
    "bienvenida": {
        "asunto": "Bienvenido/a a Gesportium",
        "cuerpo": "Hola, tu alta como socio se ha completado correctamente. ¡Te esperamos en el club!",
    },
    "plaza_liberada": {
        "asunto": "Se ha confirmado tu plaza en {clase_nombre}",
        "cuerpo": "Se ha liberado una plaza y tu reserva en '{clase_nombre}' del {clase_fecha} ha pasado a confirmada.",
    },
    "clase_reasignada": {
        "asunto": "Cambio de entrenador en {clase_nombre}",
        "cuerpo": "La clase '{clase_nombre}' del {clase_fecha} ha sido reasignada a otro entrenador.",
    },
    "clase_cancelada": {
        "asunto": "Tu clase {clase_nombre} ha sido cancelada",
        "cuerpo": "La clase '{clase_nombre}' del {clase_fecha} ha sido cancelada por baja del entrenador asignado.",
    },
    "pago_fallido": {
        "asunto": "No hemos podido procesar tu pago",
        "cuerpo": "El cobro de {importe}€ correspondiente a '{concepto}' no se ha podido procesar. Revisa tu método de pago.",
    },
    "membresia_proxima_vencer": {
        "asunto": "Tu membresía se renovará pronto",
        "cuerpo": "Tu membresía se renovará automáticamente el {fecha_renovacion}.",
    },
    "membresia_vencida": {
        "asunto": "Tu membresía ha vencido",
        "cuerpo": "Tu membresía venció el {fecha_vencimiento}. Contacta con tu sede para renovarla.",
    },
    "aforo_superado": {
        "asunto": "Aforo superado en {sede_nombre}",
        "cuerpo": "La sede {sede_nombre} ha superado su aforo máximo ({ocupacion_actual}/{aforo_maximo}).",
    },
    "marketing": {
        "asunto": "Novedades de Gesportium",
        "cuerpo": "{mensaje}",
    },
}


def renderizar(tipo: str, **contexto: str) -> tuple[str, str]:
    plantilla = PLANTILLAS[tipo]
    return plantilla["asunto"].format(**contexto), plantilla["cuerpo"].format(**contexto)
