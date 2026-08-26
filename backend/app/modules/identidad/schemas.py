import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Rol = Literal["admin", "gestor_sede", "entrenador", "socio", "comercial"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    rol: Rol
    sede_id: uuid.UUID | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UsuarioResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    rol: Rol
    sede_id: uuid.UUID | None
    activo: bool
    fecha_creacion: datetime
    fecha_ultimo_login: datetime | None

    model_config = {"from_attributes": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)
