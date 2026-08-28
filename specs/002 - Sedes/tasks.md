# Tasks 002 — Sedes

- [X] T1 — Crear modelo SQLAlchemy Sede
      Archivo: backend/app/modules/sedes/models.py
- [X] T2 — Crear migración Alembic para tabla sedes + FK en usuarios
      Archivo: backend/alembic/versions/3c005e70a49e_sedes.py
- [X] T3 — Crear schemas Pydantic (SedeCreate, SedeUpdate, SedePublic, SedeDetail)
      Archivo: backend/app/modules/sedes/schemas.py
- [X] T4 — Endpoint GET /sedes (listado público)
      Archivo: backend/app/modules/sedes/router.py
- [X] T5 — Endpoint GET /sedes/{id} (con validación de rol/pertenencia)
      Archivo: backend/app/modules/sedes/router.py
- [X] T6 — Endpoint POST /sedes (solo admin)
      Archivo: backend/app/modules/sedes/router.py
- [X] T7 — Endpoint PUT /sedes/{id} (admin o gestor_sede de esa sede)
      Archivo: backend/app/modules/sedes/router.py
- [X] T8 — Endpoint DELETE /sedes/{id} (baja lógica, solo admin)
      Archivo: backend/app/modules/sedes/router.py
- [X] T9 — Validación: no permitir baja si hay socios activos asociados
      Archivo: backend/app/modules/sedes/service.py
- [X] T10 — Tests de integración de todos los endpoints
      Archivo: backend/tests/modules/test_sedes.py (13 tests, todos en verde)
