from collections import defaultdict
from datetime import datetime, timedelta

# Limitador en memoria, de ventana deslizante, por clave (p.ej. IP). Pensado
# para endpoints públicos sin sesión donde no aplica el patrón de
# intentos_login (auditoría en BD ligada a un usuario). Suficiente para un
# único proceso; si el backend pasa a multi-worker/multi-instancia, migrar
# a un backend compartido (Redis).
_peticiones: dict[str, list[datetime]] = defaultdict(list)


def permitir(clave: str, *, max_peticiones: int, ventana_minutos: int) -> bool:
    ahora = datetime.utcnow()
    desde = ahora - timedelta(minutes=ventana_minutos)

    historial = [ts for ts in _peticiones[clave] if ts >= desde]
    if len(historial) >= max_peticiones:
        _peticiones[clave] = historial
        return False

    historial.append(ahora)
    _peticiones[clave] = historial
    return True
