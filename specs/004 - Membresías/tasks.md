# Tasks 004 — Membresías

- [X] T1 — Crear modelos SQLAlchemy (PlanMembresia, Membresia, CongelacionMembresia con campo `origen` [manual/impago], HistorialEstadosMembresia)
      Archivo: backend/app/modules/membresias/models.py
- [X] T2 — Migración Alembic para las 4 tablas
      Archivo: backend/alembic/versions/550f784f5ad2_membresias.py
- [X] T3 — Schemas Pydantic (PlanCreate, MembresiaCreate, MembresiaDetail, etc.)
      Archivo: backend/app/modules/membresias/schemas.py
- [X] T4 — Endpoints CRUD de planes de membresía
      Archivo: backend/app/modules/membresias/router.py
      Nota: implementados POST/GET (según contrato de plan.md Fase 1) + PUT (para
      cubrir "editar planes" de FR1, no listado explícitamente en la tabla de
      contratos pero sí en los requisitos funcionales)
- [X] T5 — Endpoint POST /membresias (alta)
      Archivo: backend/app/modules/membresias/router.py
- [X] T6 — Endpoint GET /membresias/{id}
      Archivo: backend/app/modules/membresias/router.py
- [X] T7 — Endpoint POST /membresias/{id}/congelar y /reactivar
      Archivo: backend/app/modules/membresias/router.py
      Nota: no existe aún infraestructura de autenticación servicio-a-servicio
      en el proyecto, así que el rol "sistema" (origen=impago) no se expone vía
      HTTP. El endpoint siempre registra origen="manual". El contrato interno
      para el módulo 008 se implementó como función Python directa,
      `service.congelar_por_impago(db, membresia)`, que el job de cobro del
      módulo 008 invocará cuando exista. Usa una cuenta técnica "sistema"
      (`service.obtener_o_crear_usuario_sistema`) como autor_id en el
      historial, sin rol reconocido por `require_roles` (no puede autenticarse).
- [X] T8 — Endpoint POST /membresias/{id}/cancelar (con validación de pagos pendientes contra módulo 008)
      Archivo: backend/app/modules/membresias/service.py
      Nota: `service.hay_pagos_pendientes` es un stub que devuelve siempre
      `False` porque el módulo 008 (Pagos) todavía no existe; documentado
      para reemplazar por la consulta real cuando se implemente ese módulo.
      `fecha_cancelacion` se calcula como hoy + `preaviso_cancelacion_dias`
      del plan, y el estado pasa a "cancelada" de inmediato (no hay tarea de
      job programado para diferir la transición de estado).
- [X] T9 — Lógica de registro automático en historial_estados_membresia (incluye cambios disparados por módulo 008 con autor_id = usuario técnico "sistema")
      Archivo: backend/app/modules/membresias/service.py
- [X] T10 — Job diario de renovación: omite membresías en estado `congelada`, marca como "próxima a vencer" (evento a módulo 011) las que estén a ≤3 días de `fecha_proxima_renovacion`
      Archivo: backend/app/modules/membresias/service.py
      Nota: implementado como función invocable (`ejecutar_job_renovacion`),
      no hay infraestructura de scheduler/cron en el proyecto todavía. El
      envío del evento al módulo 011 (Notificaciones) queda pendiente de que
      ese módulo exista; por ahora la función devuelve la lista de membresías
      próximas a vencer.
- [X] T11 — Tests de integración de todos los endpoints (incluye congelación por impago, bloqueo de reactivación y job de "próxima a vencer")
      Archivo: backend/tests/modules/test_membresias.py (17 tests, todos en verde)
