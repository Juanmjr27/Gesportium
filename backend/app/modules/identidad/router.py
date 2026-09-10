import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.identidad import service
from app.modules.identidad.dependencies import get_current_user
from app.modules.identidad.models import Usuario
from app.modules.identidad.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UsuarioResponse,
)

router = APIRouter(prefix="/auth", tags=["identidad"])

# No lanza error si falta el header: permite que /auth/register sea público
# para socios y, a la vez, autenticado para admin/gestor_sede creando cuentas.
_bearer_opcional = HTTPBearer(auto_error=False)


def _usuario_opcional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_opcional),
    db: Session = Depends(get_db),
) -> Usuario | None:
    if credentials is None:
        return None
    payload = service.decode_access_token(credentials.credentials)
    if payload is None:
        return None
    try:
        usuario_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return None
    usuario = db.get(Usuario, usuario_id)
    return usuario if usuario and usuario.activo else None


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    solicitante: Usuario | None = Depends(_usuario_opcional),
):
    if solicitante is None:
        if body.rol != "socio":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El registro público solo está permitido para socios",
            )
    elif solicitante.rol not in ("admin", "gestor_sede"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para registrar usuarios")
    elif body.rol not in ("entrenador", "socio", "comercial"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo se pueden crear cuentas de entrenador, socio o comercial",
        )

    if body.rol != "admin" and body.sede_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="sede_id es obligatorio para este rol")

    if db.query(Usuario).filter(Usuario.email == body.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado")

    usuario = service.crear_usuario(db, body.email, body.password, body.rol, body.sede_id)
    return usuario


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "desconocida"

    if service.esta_bloqueado_por_intentos(db, body.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Cuenta bloqueada temporalmente por demasiados intentos fallidos",
        )

    usuario = service.autenticar_usuario(db, body.email, body.password)
    service.registrar_intento_login(db, body.email, exitoso=usuario is not None, ip=ip)

    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    usuario.fecha_ultimo_login = datetime.utcnow()
    db.commit()

    token = service.create_access_token(usuario)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(usuario: Usuario = Depends(get_current_user)):
    # El JWT es stateless (sin tabla de tokens revocados en el modelo de
    # datos de este módulo): la invalidación real ocurre al descartar el
    # token en el cliente. El endpoint exige un token válido para simetría
    # con el resto de la API.
    return None


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == body.email).first()
    if usuario is not None:
        service.generar_token_recuperacion(db, usuario)
        # Envío real de email fuera del alcance de este módulo (fastapi-mail
        # queda declarado como dependencia externa para el módulo que lo integre).


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_recuperacion = service.resolver_token_recuperacion(db, body.token)
    if token_recuperacion is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")

    usuario = db.get(Usuario, token_recuperacion.usuario_id)
    service.cambiar_password(db, usuario, body.password, token_recuperacion)


@router.get("/me", response_model=UsuarioResponse)
def me(usuario: Usuario = Depends(get_current_user)):
    return usuario
