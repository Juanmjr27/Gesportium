# Tasks 007

- [X] T1 — Modelos SQLAlchemy (Rutina y PlanNutricional con campos `origen` [manual/ia] y `borrador_id` FK nullable a `borradores_ia` del módulo 016; EjercicioRutina, CumplimientoRutina)
      Archivo: backend/app/modules/entrenamiento/models.py
      Nota: `borrador_id` se guarda como UUID sin constraint de FK, porque la tabla `borradores_ia` (módulo 016) no existe todavía; se añadirá la FK real en una migración posterior cuando ese módulo se implemente.
- [X] T2 — Migración Alembic
      Archivo: backend/alembic/versions/11841485d0b2_entrenamiento.py
- [X] T3 — Schemas Pydantic
      Archivo: backend/app/modules/entrenamiento/schemas.py
- [X] T4 — Endpoints CRUD rutinas
      Archivo: backend/app/modules/entrenamiento/router.py
      Nota: además de POST/GET/PUT /rutinas (plan.md), se añadió GET /rutinas/{id}/cumplimiento para que el entrenador vea el progreso de su socio (FR4), no listado explícitamente en el contrato de plan.md pero requerido por la spec.
- [X] T5 — Endpoints CRUD planes nutricionales
      Archivo: backend/app/modules/entrenamiento/router.py
      Nota: se añadió PUT /planes-nutricionales/{id} (no listado en plan.md) para poder archivar/editar, igual que rutinas, y así cumplir FR5 (historial de planes archivados).
- [X] T6 — Endpoint marcar cumplimiento
      Archivo: backend/app/modules/entrenamiento/router.py
- [X] T7 — Validación entrenador-socio asignado
      Archivo: backend/app/modules/entrenamiento/router.py (`_validar_asignacion`, contra `socios_asignados` del módulo 006)
- [X] T8 — Funciones internas `crear_rutina_desde_borrador()` / `crear_plan_nutricional_desde_borrador()` en service.py: mapean `borradores_ia.contenido` (módulo 016) a los campos estructurados, fijan `origen=ia` y `borrador_id`, y devuelven error explícito (ValueError) si el mapeo falla
      Archivo: backend/app/modules/entrenamiento/service.py
- [X] T9 — Tests de integración (incluye creación de rutina/plan desde borrador IA)
      Archivo: backend/tests/modules/test_entrenamiento.py
- [X] T10 — Fix: `_validar_contenido_rutina()` rechazaba `dia_semana` con tilde (p.ej. "miércoles") porque comparaba directo contra `DIAS_SEMANA` (sin tildes) y Ollama genera los nombres de día acentuados — bug detectado durante la verificación manual de los módulos 016 T19/T21 (aprobar un borrador de rutina con ese día fallaba). Se añadió `_normalizar_dia_semana()` (minúsculas + sin tildes vía `unicodedata`) aplicada antes de comparar y de guardar, en vez de añadir "miercoles"/"miércoles" a mano, para no repetir el mismo bug con otro día acentuado en el futuro.
      Archivo: backend/app/modules/entrenamiento/service.py
      Test: backend/tests/modules/test_entrenamiento.py (test_crear_rutina_desde_borrador_con_dias_acentuados)
