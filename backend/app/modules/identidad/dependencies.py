import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identidad.models import Usuario
from app.modules.identidad.service import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    try:
        usuario_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")

    return usuario


def require_roles(*roles: str):
    def dependency(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para esta acción")
        return usuario

    return dependency


def verificar_acceso_por_sede(
    usuario: Usuario,
    sede_id: uuid.UUID,
    *,
    propietario_id: uuid.UUID | None = None,
    rol_propietario: str | None = None,
) -> None:
    if usuario.rol == "admin":
        return
    if usuario.rol == "gestor_sede" and usuario.sede_id == sede_id:
        return
    if rol_propietario and usuario.rol == rol_propietario and propietario_id == usuario.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos sobre este recurso")
