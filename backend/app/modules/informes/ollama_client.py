import httpx

from app.core.config import settings
from app.modules.informes.export import RESUMENES_INFORME, TITULOS_INFORME

TIMEOUT_SEGUNDOS = 60

PROMPT_SISTEMA = (
    "Eres un analista de datos de un gimnasio. Se te dan cifras ya calculadas "
    "de un informe. Redacta un resumen breve en español, en lenguaje natural, "
    "destacando las conclusiones más relevantes. "
    "Usa EXCLUSIVAMENTE las cifras proporcionadas a continuación: no inventes, "
    "no estimes ni menciones ningún número que no aparezca literalmente en los datos."
)


def _construir_prompt(tipo: str, datos: dict) -> str:
    hechos = "\n".join(f"- {linea}" for linea in RESUMENES_INFORME[tipo](datos))
    return (
        f"{PROMPT_SISTEMA}\n\n"
        f"Informe: {TITULOS_INFORME[tipo]}\n"
        f"Periodo: {datos['fecha_inicio']} a {datos['fecha_fin']}\n"
        f"Datos:\n{hechos}\n\n"
        "Resumen:"
    )


def generar_resumen(tipo: str, datos: dict) -> str | None:
    """Genera un resumen en lenguaje natural vía Ollama local (spec.md: "IA
    local, sin salir del servidor"). Si Ollama no está disponible (no
    arrancado, timeout, error de red), se devuelve None y el informe se
    sirve igualmente sin resumen (spec.md, criterio de aceptación).
    """
    prompt = _construir_prompt(tipo, datos)
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
