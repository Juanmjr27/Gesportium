# Tasks 001 — Identidad y Roles

- [X] T1 — Crear modelos SQLAlchemy (Usuario, IntentoLogin, TokenRecuperacion)
      Archivo: backend/app/modules/identidad/models.py
- [X] T2 — Crear migración Alembic para las 3 tablas
      Archivo: backend/alembic/versions/7b815f8fffae_identidad.py
- [X] T3 — Crear schemas Pydantic (RegisterRequest, LoginRequest, TokenResponse, etc.)
      Archivo: backend/app/modules/identidad/schemas.py
- [X] T4 — Implementar hash y verificación de contraseña (bcrypt)
      Archivo: backend/app/modules/identidad/service.py
- [X] T5 — Implementar generación y validación de JWT
      Archivo: backend/app/modules/identidad/service.py
- [X] T6 — Endpoint POST /auth/register
      Archivo: backend/app/modules/identidad/router.py
- [X] T7 — Endpoint POST /auth/login (con registro de intento en auditoría)
      Archivo: backend/app/modules/identidad/router.py
- [X] T8 — Endpoint POST /auth/logout
      Archivo: backend/app/modules/identidad/router.py
- [X] T9 — Endpoints forgot-password / reset-password
      Archivo: backend/app/modules/identidad/router.py
- [X] T10 — Dependency de validación de rol (reutilizable en futuros módulos)
      Archivo: backend/app/modules/identidad/dependencies.py
- [X] T11 — Rate limiting en login (bloqueo tras 5 intentos)
      Archivo: backend/app/modules/identidad/service.py
- [X] T12 — Tests de integración de todos los endpoints
      Archivo: backend/tests/modules/test_identidad.py (16 tests, todos en verde)