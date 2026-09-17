# Tasks 003 — Socios

- [X] T1 — Crear modelos SQLAlchemy (Socio, DocumentoSocio, NotaSocio, HistorialSedesSocio)
      Archivo: backend/app/modules/socios/models.py
- [X] T2 — Migración Alembic para las 4 tablas
      Archivo: backend/alembic/versions/bfccca424591_socios.py
- [X] T3 — Schemas Pydantic (SocioCreate, SocioUpdate, SocioDetail, SocioPublic)
      Archivo: backend/app/modules/socios/schemas.py
- [X] T4 — Endpoint POST /socios (alta)
      Archivo: backend/app/modules/socios/router.py
- [X] T5 — Endpoint GET /socios (listado filtrado por rol/sede; para entrenador, filtra por `socios_asignados` de módulo 006 unido con `reservas` de módulo 005)
      Archivo: backend/app/modules/socios/router.py
      Nota: módulos 005/006 aún no existen — entrenador recibe listado vacío hasta que se implementen (mismo patrón de referencia adelantada usado en 001/002)
- [X] T6 — Endpoint GET /socios/{id} (con exclusión de notas si es el propio socio; acceso de entrenador validado contra `socios_asignados` (006) o inscripción en clase propia (005))
      Archivo: backend/app/modules/socios/router.py
      Nota: acceso de entrenador devuelve 403 hasta que existan 005/006
- [X] T7 — Endpoint PUT /socios/{id}
      Archivo: backend/app/modules/socios/router.py
- [X] T8 — Endpoint DELETE /socios/{id} (baja lógica)
      Archivo: backend/app/modules/socios/router.py
- [X] T9 — Endpoint POST /socios/{id}/documentos (subida de archivo)
      Archivo: backend/app/modules/socios/router.py
- [X] T10 — Endpoint POST /socios/{id}/transferir (con registro en historial_sedes_socio)
      Archivo: backend/app/modules/socios/service.py
- [X] T11 — Endpoint POST /socios/{id}/notas
      Archivo: backend/app/modules/socios/router.py
- [X] T12 — Tests de integración de todos los endpoints
      Archivo: backend/tests/modules/test_socios.py (16 tests, todos en verde)

- [X] T13 — Fix: `SocioUpdate` (schemas.py) declaraba todos sus campos como `Optional`/nullable para permitir update parcial, pero las columnas correspondientes son NOT NULL en BD (models.py) — un `PUT /socios/{id}` con, p.ej., `fecha_nacimiento: null` explícito pasaba la validación de Pydantic y reventaba en la BD con un 500 en vez de un 422. Detectado durante la verificación manual del módulo 016 (T21). Se añadió un `model_validator(mode="after")` que usa `model_fields_set` para distinguir "campo omitido" (sigue permitiendo update parcial) de "campo enviado como null" (ahora rechazado con `ValueError` → 422), sin quitar `Optional` de los campos.
      Archivo: backend/app/modules/socios/schemas.py
      Test: backend/tests/modules/test_socios.py (test_put_socio_con_fecha_nacimiento_null_devuelve_422, test_put_socio_parcial_sigue_funcionando)

- [X] T14 — Fix: `CAMPOS_EDITABLES_PROPIO_SOCIO` (schemas.py) incluía `fecha_nacimiento`, permitiendo que un socio cambiase su propia fecha de nacimiento vía `PUT /socios/{id}` — contradiciendo la regla original de este módulo (T6/T7: ese campo no es editable por el propio socio) y dejando en rojo el test `test_socio_no_puede_editar_fecha_nacimiento` en CI. Se había incluido pensando en que el wizard del asistente IA (016, Paso 1) necesitaría rellenarla cuando faltase, pero ese caso resultó inalcanzable con el modelo de datos actual: `fecha_nacimiento` es `NOT NULL` en BD (models.py) y `SocioCreate` la exige siempre — ningún flujo (`POST /socios`, `POST /auth/register`) puede crear un `Socio` sin ella. Se quitó `fecha_nacimiento` de `CAMPOS_EDITABLES_PROPIO_SOCIO` y se reescribió el comentario para documentar la exclusión. Detectado verificando specs/020 (Fase 1, CI).
      Archivo: backend/app/modules/socios/schemas.py
      Test: backend/tests/modules/test_socios.py (test_socio_no_puede_editar_fecha_nacimiento)

## Trabajo adicional realizado (fuera de la lista original, solicitado explícitamente)
- Actualizada la validación de baja de sede del módulo 002 (`backend/app/modules/sedes/service.py`,
  función `tiene_socios_activos`) para consultar la entidad `Socio` real en lugar del `Usuario`
  con rol `socio` que se usaba como sustituto temporal.
