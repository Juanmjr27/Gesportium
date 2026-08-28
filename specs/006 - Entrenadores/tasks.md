# Tasks 006 — Entrenadores

- [X] T1 — Crear modelos SQLAlchemy (Entrenador, SocioAsignado)
      Archivo: backend/app/modules/entrenadores/models.py
      Nota: amplía el stub mínimo creado durante el módulo 005 (misma tabla `entrenadores`, no se recrea).
- [X] T2 — Migración Alembic para las 2 tablas
      Archivo: backend/alembic/versions/3c0486273193_entrenadores_completo.py
- [X] T3 — Schemas Pydantic (EntrenadorCreate, EntrenadorDetail, etc.)
      Archivo: backend/app/modules/entrenadores/schemas.py
- [X] T4 — Endpoints CRUD de entrenadores
      Archivo: backend/app/modules/entrenadores/router.py
- [X] T5 — Endpoint POST/DELETE asignación de socios
      Archivo: backend/app/modules/entrenadores/router.py
      Nota: roles admin + gestor_sede (plan.md solo listaba gestor_sede; ampliado a petición del usuario para consistencia con el resto de endpoints de gestión).
- [X] T6 — Endpoint GET /entrenadores/{id}/socios
      Archivo: backend/app/modules/entrenadores/router.py
- [X] T7 — Validación de baja: comprobar clases futuras (módulo 005); si existen, requerir confirmación del gestor_sede y, al confirmar, llamar a `POST /clases/reasignar-por-baja-entrenador` (módulo 005) para reasignarlas o cancelarlas
      Archivo: backend/app/modules/entrenadores/service.py
      Nota: la llamada al módulo 005 se hace como invocación directa de `clases.service.reasignar_por_baja_entrenador` (contrato interno de servicio), no como petición HTTP saliente, siguiendo el mismo patrón ya usado en membresías/service.py para el contrato con el módulo 008.
- [X] T8 — Tests de integración de todos los endpoints
      Archivo: backend/tests/modules/test_entrenadores.py
