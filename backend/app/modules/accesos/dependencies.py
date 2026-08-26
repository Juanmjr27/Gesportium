from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_totem_device(x_totem_key: str | None = Header(default=None)) -> None:
    """Autenticación de dispositivo (tótem/tablet de sede), no de usuario.

    plan.md deja "a definir en detalle en implementación": no existe
    infraestructura de auth por dispositivo en el proyecto, así que se
    resuelve con la opción más simple —una clave compartida por cabecera,
    comparable a una API key de servicio— en vez de JWT de usuario, que
    exigiría una cuenta humana logueada en el tótem.
    """
    if x_totem_key != settings.totem_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Dispositivo no autorizado")
