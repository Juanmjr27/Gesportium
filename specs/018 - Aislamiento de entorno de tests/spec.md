# Spec 018 — Aislamiento de entorno de tests

## Resumen
Backend de infraestructura: la suite de pytest y el servidor de desarrollo
(`uvicorn`, usado en verificaciones manuales/Playwright contra
`localhost:8000`) comparten la misma base de datos PostgreSQL. Esto hace que
la suite de tests sea no determinista según qué se haya probado a mano justo
antes de correrla.

## Relación con módulos existentes
- No añade funcionalidad de producto: es infraestructura de desarrollo
  (`backend/tests/conftest.py`, configuración de BD)
- Afecta transversalmente a todos los módulos backend (001–017), ya que
  todos comparten el mismo `conftest.py`

## Problema observado
`db_session` (fixture de `backend/tests/conftest.py`) aísla cada test con su
propia transacción (SAVEPOINT + rollback al terminar), pero esa transacción
vive en la misma base de datos PostgreSQL (`DATABASE_URL`) que usa el
servidor real cuando se levanta con `uvicorn` para verificación manual. El
aislamiento de `db_session` solo protege a un test de OTRO test dentro de la
misma suite — no protege a la suite de lo que un proceso externo (el
servidor real) haya comprometido (`commit`) en esa misma base de datos.

Efecto: tests que asumen una tabla vacía o un conteo concreto al empezar
(p. ej. `assert db_session.query(BorradorIA).count() == 0`, o un endpoint que
numera facturas/borradores contando filas existentes) fallan de forma no
determinista según qué se haya probado a mano contra `localhost:8000` justo
antes — con Playwright, `curl`, o scripts sueltos de verificación
(`verify_bugs.mjs` y similares).

Ya ha ocurrido dos veces, documentado en tasks.md de otros módulos:
- Módulo 016, T10: verificación manual de un borrador de IA dejó filas en
  `borradores_ia` que hicieron fallar un test de otro módulo.
- Módulo 003, verificación de T13: `test_asistente_ia.py::test_borrador_si_
  ollama_no_responde_devuelve_503` falló por 24 filas sueltas de
  `BorradorIA` dejadas por sesiones de verificación manual previas (T19/T21
  de 016, T10 de 007) — confirmado no ser una regresión del propio T13
  desactivando temporalmente su código y viendo el mismo fallo.

## Requisitos funcionales
1. La suite de pytest debe usar una base de datos distinta a la que usa el
   servidor de desarrollo (`uvicorn`), en la misma instancia de PostgreSQL,
   para no depender de SQLite ni de mocks del motor (el resto del proyecto
   usa PostgreSQL real; ver plan.md)
2. La base de datos de test debe poder crearse automáticamente si no existe
   (sin pasos manuales obligatorios para levantar el proyecto en local),
   siempre que el usuario de BD configurado tenga privilegio `CREATEDB`
3. La base de datos de test debe construirse ejecutando las migraciones
   reales de Alembic (`alembic upgrade head`), no solo el esquema de los
   modelos (`Base.metadata.create_all()`), para que los datos sembrados por
   migraciones de datos (p. ej. `configuracion_global` en la migración
   `deb0740ca027`) también existan en test — de lo contrario, tests que
   dependen de esos datos sembrados fallan en una BD de test recién creada
   aunque nunca hayan tenido relación con el bug de aislamiento original
4. Debe seguir siendo posible apuntar la BD de test a una URL explícita
   (variable de entorno), para entornos donde el desarrollador prefiera
   gestionarla manualmente (p. ej. CI)
5. Las filas sueltas ya existentes en la base de datos de desarrollo,
   dejadas por sesiones de verificación manual anteriores (24 filas de
   `BorradorIA` y sus dependientes en cascada: usuarios, socios,
   entrenadores, rutinas, planes nutricionales, etc. con emails de un solo
   uso tipo `ia-t21-socio-<timestamp>@test.com`), deben limpiarse como parte
   de esta feature — sin tocar los usuarios de humo estables y reutilizados
   entre sesiones (`smoke-admin@test.com`, `smoke-entrenador@test.com`,
   `smoke-socio@test.com`)

## Criterios de aceptación
- Correr la suite completa de pytest dos veces seguidas da el mismo
  resultado exacto (mismos tests en verde, mismos tests en rojo)
- Correr la suite completa justo después de una sesión de verificación
  manual (Playwright, `curl`, scripts sueltos) contra el servidor real de
  desarrollo tampoco cambia el resultado
- La base de datos de desarrollo (`DATABASE_URL`) no se modifica al correr
  pytest: ninguna fila de test se escribe ahí
- La base de datos de test se crea sola en un checkout nuevo del proyecto,
  sin pasos manuales, siempre que el usuario de BD tenga `CREATEDB`

## Fuera de alcance en esta feature
- Migrar la suite a SQLite o a un motor mockeado (rompería la paridad con
  PostgreSQL real que usa el resto del proyecto)
- Paralelización de tests (`pytest-xdist` o similar) — el aislamiento
  resuelto aquí es entre pytest y el servidor real, no entre workers de
  pytest entre sí
- Cualquier fuente de no-determinismo de test que no dependa de datos
  compartidos con el servidor de desarrollo. En particular, durante la
  verificación de esta feature se detectó un flake **no relacionado**
  (colisión del nombre de fichero PDF de factura, ver tasks.md T5): se deja
  documentado como hallazgo, no se corrige aquí
