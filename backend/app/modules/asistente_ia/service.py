import json
import uuid
from datetime import date
 
import httpx
from sqlalchemy.orm import Session
 
from app.core.config import settings
from app.modules.asistente_ia.models import ConversacionIA, MensajeIA
 
TIMEOUT_SEGUNDOS = 60
 
PROMPT_SISTEMA_CHAT = (
    "Eres el asistente virtual de un gimnasio. Respondes dudas generales de "
    "socios sobre horarios, qué incluye su membresía y cómo reservar clases. "
    "No das diagnósticos médicos ni consejos de salud fuera de nutrición y "
    "ejercicio general: si te lo piden, recomienda consultar a un profesional."
)
 
FORMATOS_BORRADOR = {
    "rutina": (
        '{"nombre": "<texto>", "ejercicios": [{"nombre": "<texto>", "series": <numero>, '
        '"repeticiones": <numero>, "dia_semana": "<lunes|martes|miercoles|jueves|viernes|sabado|domingo>", '
        '"descanso_segundos": <numero>}]}'
    ),
    "plan_nutricional": '{"nombre": "<texto>", "notas": "<texto>"}',
}
 
# Etiquetas legibles para volcar el dict de datos_cuestionario en el prompt,
# en el mismo orden que los pasos del wizard (spec 016).
_ETIQUETAS_CUESTIONARIO = {
    "sexo": "sexo",
    "peso_kg": "peso",
    "altura_cm": "altura",
    "nivel_actividad_actual": "nivel de actividad actual",
    "restricciones_medicas": "restricciones médicas/alergias",
    "dias_disponibles_semana": "días disponibles a la semana",
    "equipamiento": "equipamiento disponible",
    "lesiones_zonas_evitar": "lesiones o zonas a evitar",
    "preferencia_alimentaria": "preferencia alimentaria",
    "comidas_al_dia": "comidas al día",
    "alimentos_excluir": "alimentos a excluir",
    "objetivo_principal": "objetivo principal",
    "objetivo_detalle": "detalle del objetivo",
}
 
 
def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
 
 
def obtener_o_crear_conversacion(db: Session, socio_id: uuid.UUID) -> ConversacionIA:
    conversacion = db.query(ConversacionIA).filter(ConversacionIA.socio_id == socio_id).first()
    if conversacion is None:
        conversacion = ConversacionIA(socio_id=socio_id)
        db.add(conversacion)
        db.commit()
        db.refresh(conversacion)
    return conversacion
 
 
def registrar_mensaje(db: Session, conversacion_id: uuid.UUID, rol: str, contenido: str) -> MensajeIA:
    mensaje = MensajeIA(conversacion_id=conversacion_id, rol=rol, contenido=contenido)
    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)
    return mensaje
 
 
def generar_respuesta_chat(historial: list[str], mensaje: str) -> str | None:
    """Genera la respuesta del chat vía Ollama local (mismo servicio que el
    módulo 013, plan.md Fase 2). Si Ollama no responde, devuelve None para
    que el router informe el fallo sin bloquear el resto de la app
    (spec.md, criterio de aceptación).
    """
    contexto = "\n".join(historial)
    prompt = f"{PROMPT_SISTEMA_CHAT}\n\n{contexto}\nSocio: {mensaje}\nAsistente:"
    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=TIMEOUT_SEGUNDOS,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None
 
    texto = response.json().get("response", "").strip()
    return texto or None
 
 
def _describir_datos_cuestionario(datos_cuestionario: dict) -> str:
    """Convierte el dict de WizardBorradorRequest (schemas.py) en una lista
    legible para el prompt, en el orden de los pasos del wizard (spec 016).
    Solo incluye lo que el socio realmente rellenó — el router ya envía el
    dict con exclude_none=True."""
    lineas = [
        f"- {_ETIQUETAS_CUESTIONARIO.get(clave, clave)}: {valor}"
        for clave, valor in datos_cuestionario.items()
        if clave != "tipo_borrador" and valor is not None
    ]
    return "\n".join(lineas)
 
 
def generar_contenido_borrador(
    tipo: str, edad: int, datos_cuestionario: dict, plan_membresia: str | None
) -> dict | None:
    """Genera el JSON de un borrador de rutina/plan nutricional vía Ollama,
    a partir de las respuestas completas del cuestionario guiado (spec 016).
    Devuelve None si Ollama no responde o si la respuesta no es un JSON
    válido, para que el router rechace la solicitud en vez de crear un
    borrador con contenido corrupto.
    """
    prompt = (
        "Eres el asistente de un gimnasio que redacta borradores personalizados "
        "que después debe revisar y aprobar un entrenador humano. No das "
        "diagnósticos médicos. Responde EXCLUSIVAMENTE con un JSON válido, sin "
        f"texto adicional, con este formato exacto: {FORMATOS_BORRADOR[tipo]}\n\n"
        f"Datos del socio: edad {edad} años, membresía: {plan_membresia or 'sin membresía activa'}.\n"
        f"Respuestas del cuestionario:\n{_describir_datos_cuestionario(datos_cuestionario)}"
    )
    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
            timeout=TIMEOUT_SEGUNDOS,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return None
 
    texto = response.json().get("response", "").strip()
    try:
        contenido = json.loads(texto)
    except json.JSONDecodeError:
        return None
    return contenido if isinstance(contenido, dict) else None
 