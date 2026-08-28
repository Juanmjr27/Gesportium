# Tasks 009

- [X] T1 — Modelo SQLAlchemy Acceso
      Archivo: backend/app/modules/accesos/models.py
- [X] T2 — Migración Alembic
      Archivo: backend/alembic/versions/7e1b8b7d131e_accesos.py
- [X] T3 — Schemas Pydantic
      Archivo: backend/app/modules/accesos/schemas.py
- [X] T4 — Endpoint POST /accesos/checkin (valida membresía, marca asistencia si aplica)
      Archivos: backend/app/modules/accesos/router.py, service.py, dependencies.py
      Nota: plan.md deja la autenticación de dispositivo "a definir en detalle en implementación" — no existe infraestructura de auth por dispositivo en el proyecto (ni JWT de usuario tiene sentido para un tótem sin usuario logueado). Se resolvió con una clave compartida por cabecera `X-Totem-Key` (`settings.totem_api_key`, dependencia `require_totem_device`), la opción más simple consistente con el resto de auth del proyecto.
      Nota: el endpoint alterna automáticamente entre `entrada`/`salida` según el último acceso registrado del socio en esa sede (spec.md no distingue una ruta por tipo). La sede se recibe en el body ya que no existe un mecanismo de "tótem fijo a una sede" en el modelo de datos.
      Nota: la marca de asistencia usa el contrato ya establecido `clases/service.py::checkin_asistencia` (no escribe directamente en tablas del módulo 005), buscando una reserva `confirmada` cuya clase esté en curso (entre `fecha_hora` y `fecha_hora + duracion_minutos`) en el momento del check-in.
- [X] T5 — Endpoint GET /sedes/{id}/aforo-actual (cálculo en tiempo real)
      Archivo: backend/app/modules/accesos/router.py, service.py (`calcular_aforo_actual`)
      Nota: ocupación = socios cuyo último acceso registrado en la sede es de tipo `entrada`. Criterio de aceptación "se avisa a gestor_sede, no bloquea": se devuelve `aforo_superado` para que el rol lo vea en este endpoint; el aviso proactivo queda pendiente del módulo 011 (Notificaciones), mismo patrón que otros eventos ya documentados en clases/service.py y pagos/service.py.
- [X] T6 — Endpoint historial de accesos
      Archivo: backend/app/modules/accesos/router.py (GET /accesos/{socio_id})
- [X] T7 — Tests de integración
      Archivo: backend/tests/modules/test_accesos.py
