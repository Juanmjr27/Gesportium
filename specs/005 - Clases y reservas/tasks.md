# Tasks 005 — Clases y reservas

- [X] T1 — Crear modelos SQLAlchemy (Clase con `entrenador_id` FK a `entrenadores.id` del módulo 006, Reserva, Asistencia)
      Archivo: backend/app/modules/clases/models.py
- [X] T2 — Migración Alembic para las 3 tablas (FK `clases.entrenador_id` → `entrenadores.id`)
      Archivo: backend/alembic/versions/7e72da7f8741_entrenadores_stub_y_clases.py
      Nota: incluye también un stub mínimo de `entrenadores` (backend/app/modules/entrenadores/models.py), acordado con el usuario porque el módulo 006 aún no existe.
- [X] T3 — Schemas Pydantic (ClaseCreate, ReservaCreate, ClaseDetail, etc.)
      Archivo: backend/app/modules/clases/schemas.py
- [X] T4 — Endpoint POST /clases y PUT /clases/{id} (valida que `entrenador_id` exista en módulo 006 con `activo=true` antes de asignar)
      Archivo: backend/app/modules/clases/router.py
- [X] T5 — Endpoint GET /clases con filtros (sede, fecha)
      Archivo: backend/app/modules/clases/router.py
- [X] T6 — Endpoint POST /clases/{id}/reservar (con validación de membresía y aforo)
      Archivo: backend/app/modules/clases/service.py
- [X] T7 — Lógica de lista de espera y promoción automática al liberarse plaza
      Archivo: backend/app/modules/clases/service.py
- [X] T8 — Endpoint DELETE /reservas/{id}
      Archivo: backend/app/modules/clases/router.py
- [X] T9 — Endpoint GET /clases/{id}/ocupacion
      Archivo: backend/app/modules/clases/router.py
- [X] T10 — Endpoint interno POST /clases/reasignar-por-baja-entrenador (rol sistema/gestor_sede), invocado por módulo 006 al dar de baja un entrenador: reasigna o cancela sus clases futuras y notifica a socios con reserva confirmada (módulo 011)
      Archivo: backend/app/modules/clases/router.py
- [X] T11 — Tests de integración de todos los endpoints (incluye validación de entrenador activo y reasignación/cancelación por baja)
      Archivo: backend/tests/modules/test_clases.py
