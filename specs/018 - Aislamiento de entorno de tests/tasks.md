# Tasks 018 — Aislamiento de entorno de tests

- [X] T1 — Añadir `test_database_url: str | None = None` a `Settings`, y
      documentar `TEST_DATABASE_URL` (opcional) en `.env.example` con el
      comportamiento por defecto si se omite
      Archivo: backend/app/core/config.py, backend/.env.example
- [X] T2 — `backend/tests/conftest.py`: resolver la URL de BD de test
      (env var o `DATABASE_URL` + sufijo `_test`), crear la base si no
      existe (requiere `CREATEDB`, confirmado disponible en el usuario de
      BD del proyecto), y construirla ejecutando `alembic upgrade head`
      (no `Base.metadata.create_all()`) para incluir también los datos
      sembrados por migraciones de datos (p. ej. `configuracion_global`).
      La fixture `db_session` pasa a usar este motor de test en vez del
      `engine` compartido con la app real
      Archivo: backend/tests/conftest.py
- [X] T3 — Limpiar las filas sueltas de la BD de desarrollo dejadas por
      sesiones de verificación manual anteriores: 29 usuarios de un solo
      uso y todo lo que dependía de ellos en cascada (23 de 24 filas de
      `BorradorIA`, socios, entrenadores, rutinas, planes nutricionales,
      asignaciones, notificaciones, historial, clases), preservando la
      cuenta de humo estable (`smoke-admin@test.com`,
      `smoke-entrenador@test.com`, `smoke-socio@test.com`) y su fila de
      `BorradorIA`. Script puntual, no forma parte del código de la app
      Verificación: `SELECT count(*) FROM borradores_ia` pasó de 24 a 1;
      `SELECT count(*) FROM usuarios WHERE email LIKE '%test.com%'` pasó
      de 32 a 3 (solo las smoke-*)
- [X] T4 — Verificar el criterio de aceptación de spec.md: correr la suite
      completa dos veces seguidas, y una vez más justo después de una
      sesión de verificación manual contra el servidor real
      (`localhost:8000`, con Playwright/scripts sueltos), y confirmar que
      el resultado no cambia y que `DATABASE_URL` (BD de desarrollo) no
      recibe ninguna fila de test
      Resultado: 261 passed / 1 failed, idéntico antes y después de la
      verificación manual (el único fallo es
      `test_socios.py::test_socio_no_puede_editar_fecha_nacimiento`, un
      test desactualizado y sin relación con este módulo — ver nota de T4b)
- [X] T4b — Nota sobre determinismo no perfecto: en un tercer run de
      control (sin verificación manual de por medio) apareció además
      `test_pagos.py::test_socio_descarga_su_propia_factura` en rojo, un
      flake intermitente **no causado** por el problema de aislamiento que
      resuelve este módulo (confirmado: `test_pagos.py` en solitario pasa
      3/3 veces de forma estable) — ver T5 para el diagnóstico completo.
      Este módulo dejó determinista la parte del problema que le
      correspondía (contaminación cruzada pytest↔servidor real); T5 queda
      documentado como hallazgo aparte, no como parte del criterio de
      aceptación de este módulo
- [X] T5 — (Hallazgo, no fix) Diagnosticado el flake de T4b:
      `_siguiente_numero_factura()` (`backend/app/modules/pagos/service.
      py`) numera facturas contando filas de `Factura` dentro de la propia
      transacción del test; como cada test empieza con la tabla vacía,
      varios tests que emiten su primera factura calculan el mismo
      `numero` (`F-2026-000001`), y `generar_pdf_factura()` escribe el PDF
      a `storage/facturas/{numero}.pdf` — mismo nombre de fichero en
      disco, fuera de la transacción de BD y por tanto no cubierto por el
      rollback de `db_session`, lo que produce fallos intermitentes en
      Windows al re-escribirse el mismo fichero entre tests. Recomendación
      si se decide corregir en otra tarea: incluir un identificador único
      (p. ej. `pago.id`) en el nombre de fichero físico, sin tocar el
      campo `numero` de negocio que ve el usuario
      Archivo: backend/app/modules/pagos/service.py,
      backend/app/modules/pagos/pdf.py

      **Confirmación empírica (2026-08-26):** reproducido de forma
      controlada corriendo `tests/modules/test_pagos.py` en solitario 8
      veces seguidas (sin ningún otro módulo ni verificación manual de
      por medio): 2 de 8 runs fallaron, ambos con el mismo traceback:
      ```
      FAILED tests/modules/test_pagos.py::test_cobro_exitoso_audita_pago_y_factura
      PermissionError: [Errno 13] Permission denied:
      '...\backend\storage\facturas\F-2026-000001.pdf'
      ```
      Confirma que la causa es exactamente la del diagnóstico: colisión
      de `numero` entre tests que reescriben el mismo fichero físico
      (`test_cobro_exitoso_genera_factura` u otro test anterior en el
      mismo run ya había creado `F-2026-000001.pdf`), no un efecto
      secundario del cambio de BD de test de este módulo. El mismo test
      en solitario (`pytest ... ::test_cobro_exitoso_audita_pago_y_factura`)
      pasó 6/6 veces — el fallo solo aparece cuando otro test del mismo
      fichero ya escribió ese `numero` antes en el mismo proceso.
      **No afecta al criterio de aceptación de specs/018**: ese criterio
      es específicamente sobre la contaminación pytest↔servidor real
      (BD de desarrollo compartida), que quedó resuelta y verificada por
      separado (T4). Esta es una causa de no-determinismo distinta y
      preexistente al aislamiento de BD, dentro del propio `conftest.py`/
      suite, no entre pytest y el servidor externo — de ahí que se
      mantenga fuera de alcance de este módulo, pero ya no es solo un
      hallazgo teórico: es un bug real y reproducible, y se recomienda
      abrirlo como tarea de corrección aparte con prioridad (afecta a la
      fiabilidad de la suite en CI, no solo en local).

      **Corregido de raíz (2026-08-27):** ver `specs/008 - Pagos y
      facturación/tasks.md` T11. `numero` de factura pasa a derivarse de
      una SEQUENCE de Postgres (atómica y no transaccional) en vez de
      contar filas dentro de la transacción del caller. Verificado con
      `tests/modules/test_pagos.py` en solitario, 30 rondas seguidas, 0
      fallos.
- [X] T6 — `.env.example` ya documenta `TEST_DATABASE_URL` (T1); no existe
      `README.md` en el proyecto (es el único mecanismo de documentación
      de setup usado hasta ahora), así que no se crea uno nuevo solo para
      esto — mismo criterio que el resto del proyecto
