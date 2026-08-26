import secrets
import uuid
from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.identidad.models import IntentoLogin, TokenRecuperacion, Usuario

BCRYPT_ROUNDS = 12

RATE_LIMIT_MAX_INTENTOS = 5
RATE_LIMIT_VENTANA_MINUTOS = 15
RESET_TOKEN_VALIDEZ_HORAS = 1


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(usuario: Usuario) -> str:
    expira = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    payload = {
        "sub": str(usuario.id),
        "rol": usuario.rol,
        "sede_id": str(usuario.sede_id) if usuario.sede_id else None,
        "exp": expira,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def esta_bloqueado_por_intentos(db: Session, email: str) -> bool:
    desde = datetime.utcnow() - timedelta(minutes=RATE_LIMIT_VENTANA_MINUTOS)
    fallidos = (
        db.query(func.count(IntentoLogin.id))
        .filter(
            IntentoLogin.usuario_email == email,
            IntentoLogin.exitoso.is_(False),
            IntentoLogin.fecha >= desde,
        )
        .scalar()
    )
    return fallidos >= RATE_LIMIT_MAX_INTENTOS


def registrar_intento_login(db: Session, email: str, exitoso: bool, ip: str) -> None:
    intento = IntentoLogin(usuario_email=email, exitoso=exitoso, ip=ip, fecha=datetime.utcnow())
    db.add(intento)
    db.commit()


def autenticar_usuario(db: Session, email: str, password: str) -> Usuario | None:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not usuario.activo:
        return None
    if not verify_password(password, usuario.password_hash):
        return None
    return usuario


def crear_usuario(db: Session, email: str, password: str, rol: str, sede_id: uuid.UUID | None) -> Usuario:
    usuario = Usuario(
        email=email,
        password_hash=hash_password(password),
        rol=rol,
        sede_id=sede_id,
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def generar_token_recuperacion(db: Session, usuario: Usuario) -> TokenRecuperacion:
    token = TokenRecuperacion(
        usuario_id=usuario.id,
        token=secrets.token_urlsafe(32),
        expira=datetime.utcnow() + timedelta(hours=RESET_TOKEN_VALIDEZ_HORAS),
        usado=False,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def resolver_token_recuperacion(db: Session, token: str) -> TokenRecuperacion | None:
    registro = db.query(TokenRecuperacion).filter(TokenRecuperacion.token == token).first()
    if not registro or registro.usado or registro.expira < datetime.utcnow():
        return None
    return registro


def cambiar_password(db: Session, usuario: Usuario, nueva_password: str, token_recuperacion: TokenRecuperacion) -> None:
    usuario.password_hash = hash_password(nueva_password)
    token_recuperacion.usado = True
    db.commit()
