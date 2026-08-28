# Plan 001 — Identidad y Roles

## Arquitectura técnica

## Fase 0 — Modelo de datos (SQLAlchemy)

**Tabla `usuarios`**
- id (UUID, PK)
- email (string, único)
- password_hash (string)
- rol (enum: admin, gestor_sede, entrenador, socio, comercial)
- sede_id (FK a sedes, nullable — admin no pertenece a una sede)
- activo (boolean, default true)
- fecha_creacion (datetime)
- fecha_ultimo_login (datetime, nullable)

**Tabla `intentos_login`** (auditoría)
- id (UUID, PK)
- usuario_email (string)
- exitoso (boolean)
- ip (string)
- fecha (datetime)

**Tabla `tokens_recuperacion`**
- id (UUID, PK)
- usuario_id (FK a usuarios)
- token (string, único)
- expira (datetime)
- usado (boolean, default false)

## Fase 1 — Contratos de API

| Método | Ruta | Rol requerido | Descripción |
|---|---|---|---|
| POST | /auth/register | público (solo socio) o admin/gestor_sede (socio, entrenador, comercial) | Registro de usuario |
| POST | /auth/login | público | Login, devuelve JWT |
| POST | /auth/logout | autenticado | Invalida token |
| POST | /auth/forgot-password | público | Solicita recuperación |
| POST | /auth/reset-password | público (con token) | Cambia contraseña |
| GET | /auth/me | autenticado | Datos del usuario actual |

## Fase 2 — Seguridad
- Contraseñas: bcrypt (12 rounds)
- JWT: expiración 24h, firmado con clave secreta en variable de entorno
- Middleware de FastAPI valida rol en cada endpoint protegido (dependency injection)
- Rate limiting en /auth/login: bloqueo tras 5 intentos fallidos en 15 min

## Fase 3 — Estructura de carpetas (backend)

\`\`\`
backend/
└── app/
    └── modules/
        └── identidad/
        ├── models.py # Usuario, IntentoLogin, TokenRecuperacion
        ├── schemas.py # Pydantic schemas (request/response)
        ├── router.py # Endpoints FastAPI
        ├── service.py # Lógica de negocio
        └── dependencies.py # Validación de rol/JWT (reutilizable por otros módulos)
\`\`\`

## Fase 4 — Dependencias externas
- `python-jose` (JWT)
- `passlib[bcrypt]` (hash de contraseñas)
- `fastapi-mail` (envío de emails de recuperación)