# Plan 018 — Aislamiento de entorno de tests

## Contexto técnico actual (antes de este plan)
- `backend/app/core/config.py`: `Settings.database_url: str` (obligatorio,
  vía `.env`); un único `DATABASE_URL` para toda la app
- `backend/app/core/database.py`: `engine = create_engine(settings.
  database_url)` a nivel de módulo — el motor que usa tanto la app real
  (`uvicorn`) como, hasta ahora, los tests
- `backend/tests/conftest.py`: `Base.metadata.create_all(bind=engine)` a
  nivel de módulo (crea el esquema si falta, en la MISMA BD que usa
  `uvicorn`); fixture `db_session` abre una conexión de ese mismo `engine`,
  envuelve el test en una transacción con SAVEPOINT y hace rollback al
  terminar — aísla tests entre sí, no aísla la suite del servidor real
- No hay ninguna BD de test distinta configurada ni documentada

## Fase 0 — Diagnóstico (ya validado en sesión, ver spec.md)
El problema no es el mecanismo de rollback de `db_session` (funciona
correctamente para aislar tests entre sí) — es que su punto de partida
(el estado de la BD antes de `connection.begin()`) incluye todo lo que el
servidor de desarrollo haya comprometido ahí mismo.

## Fase 1 — Solución: BD de test separada, misma instancia PostgreSQL
Se descarta SQLite/mocks del motor (rompería paridad con Postgres real,
usado en producción y por el resto del proyecto — tipos como `UUID`,
`JSONB` de PostgreSQL no son portables a SQLite sin reescribir modelos).

Se añade una segunda base de datos, en la misma instancia de PostgreSQL que
`DATABASE_URL`, resuelta así (en orden de prioridad):
1. Variable de entorno `TEST_DATABASE_URL` (opcional, en `.env`), para
   quien quiera gestionarla explícitamente (p. ej. CI con una BD de test ya
   provisionada)
2. Si no está definida: se deriva de `DATABASE_URL` añadiendo `_test` al
   nombre de la base (`gesportium` → `gesportium_test`), sobre la misma
   instancia/usuario — cero configuración adicional para desarrollo local

`backend/app/core/config.py` gana un campo `test_database_url: str | None
= None`.

## Fase 2 — Construcción de la BD de test
`backend/tests/conftest.py`, a nivel de módulo (una vez por sesión de
pytest, no por test):
1. Si la base de datos de test no existe todavía, se crea (`CREATE
   DATABASE`, requiere que el usuario de BD configurado tenga privilegio
   `CREATEDB` — confirmado disponible en el usuario `gesportium` de este
   proyecto)
2. Se ejecuta `alembic upgrade head` contra esa BD (no `Base.metadata.
   create_all()`) — necesario porque hay migraciones de datos (`op.
   bulk_insert`), no solo de esquema: la migración `deb0740ca027`
   (módulo 014, configuración) siembra `configuracion_global` con las
   claves `moneda`/`zona_horaria`/`texto_politica_privacidad`/
   `texto_condiciones`, y al menos un test (`test_configuracion.py::
   test_admin_lista_configuracion_incluye_parametros_sembrados`) depende de
   que existan. `create_all()` solo crea tablas vacías; usar las
   migraciones reales también da paridad exacta con cómo se construye la
   BD de producción, no una aproximación
3. Reintentos: `alembic upgrade head` sobre una BD ya al día es una
   operación idempotente (Alembic compara contra su tabla
   `alembic_version`), así que correr la suite repetidamente no repite
   trabajo innecesario

La fixture `db_session` pasa a abrir su conexión sobre este nuevo motor de
test (antes usaba el `engine` de `app.core.database`, compartido con la
app real) — el resto de su lógica (SAVEPOINT + rollback) no cambia.

## Fase 3 — Limpieza de la BD de desarrollo
Antes de dar la feature por completa, se limpian las filas sueltas ya
existentes en `DATABASE_URL` (no en la BD de test, que nace limpia): 29
usuarios de un solo uso (`ia-t21-socio-*`, `verify-bugs-*`, `t14wizard@test.
com`, etc.) y todo lo que depende de ellos en cascada (socios, entrenadores,
23 de las 24 filas de `BorradorIA`, rutinas, planes nutricionales,
asignaciones, notificaciones, historial, clases). Se conservan
`smoke-admin@test.com`/`smoke-entrenador@test.com`/`smoke-socio@test.com`
(cuenta de humo estable, reutilizada a propósito entre sesiones de
verificación, no un residuo de una sola sesión) y la fila de `BorradorIA`
que le pertenece.

Método: script puntual (no forma parte del código de la app) que recorre el
grafo de FKs ya declarado en `Base.metadata` de SQLAlchemy — no una lista de
tablas mantenida a mano — para borrar en el orden correcto (hijos antes que
padres) todo lo que cuelga transitivamente de esos usuarios. Se ejecuta una
vez como parte de esta feature; no se deja como parte del código de
producción ni de los tests.

## Fase 4 — Estructura de archivos afectados
```
backend/
├── .env.example                        (documenta TEST_DATABASE_URL)
├── app/core/config.py                  (+ test_database_url)
└── tests/conftest.py                   (BD de test separada + alembic upgrade)
```

## Fase 5 — Documentación
`.env.example` ya es el mecanismo de documentación de configuración del
proyecto (no existe `README.md`): se añade `TEST_DATABASE_URL` ahí, con un
comentario explicando el comportamiento por defecto (auto-derivado,
auto-creado) para que quien levante el proyecto en local no necesite ningún
paso manual salvo tener PostgreSQL corriendo con un usuario con `CREATEDB`.

## Fase 6 — Hallazgo colateral (documentado, no corregido aquí)
Verificando el criterio de aceptación (correr la suite dos veces seguidas)
se detectó un segundo tipo de no-determinismo, ya sin relación con el
aislamiento pytest↔servidor real: `_siguiente_numero_factura()`
(`backend/app/modules/pagos/service.py`) calcula el número de factura
como `F-{año}-{count(Factura)+1:06d}` dentro de la propia transacción del
test — como cada test aislado empieza con `Factura` vacía, dos tests
distintos que emiten su primera factura calculan el mismo número
(`F-2026-000001`), y `generar_pdf_factura()` escribe el PDF a
`storage/facturas/{numero}.pdf`: el mismo nombre de fichero en disco,
fuera de cualquier transacción de BD y por tanto no protegido por el
rollback de `db_session`. Produce fallos intermitentes en Windows
(bloqueo de fichero) al re-escribirse el mismo PDF entre tests. No se
corrige en esta feature (no es aislamiento pytest↔servidor real); ver
tasks.md T5 para el detalle y la recomendación de fix si se decide
abordarlo en otra tarea.
