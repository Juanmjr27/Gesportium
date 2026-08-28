# Tasks 008

- [X] T1 — Modelos SQLAlchemy (Pago, Factura, Remesa, RemesaPago)
      Archivo: backend/app/modules/pagos/models.py
      Nota: Pago añade `intentos` (contador de reintentos) y `periodo` (fecha de renovación facturada), no listados en plan.md pero necesarios para T4/T8 y para el criterio "no se puede facturar dos veces el mismo periodo".
- [X] T2 — Migración Alembic
      Archivo: backend/alembic/versions/266853c6c8d4_pagos.py
- [X] T3 — Schemas Pydantic
      Archivo: backend/app/modules/pagos/schemas.py
- [X] T4 — Lógica de cobro automático + reintentos por impago (excluye membresías en estado `congelada`, consultado vía módulo 004)
      Archivo: backend/app/modules/pagos/service.py (`procesar_cobros_automaticos`, `generar_cobro_pendiente`, `intentar_cobro`)
      Nota: no expuesto como endpoint HTTP — ver nota en T8.
- [X] T5 — Generación de factura PDF
      Archivo: backend/app/modules/pagos/pdf.py (reportlab, añadido a requirements.txt); PDFs en backend/storage/facturas/ (gitignored)
- [X] T6 — Endpoint historial de pagos
      Archivo: backend/app/modules/pagos/router.py (GET /pagos/{socio_id}, GET /facturas/{id} para descarga)
- [X] T7 — Endpoint generación/listado de remesas
      Archivo: backend/app/modules/pagos/router.py (POST /remesas, GET /remesas)
- [X] T8 — Trigger: tras N impagos, llamar a `POST /membresias/{id}/congelar` (módulo 004) con `origen=impago` — único mecanismo autorizado, sin escritura directa en BD de 004
      Archivo: backend/app/modules/pagos/service.py (`intentar_cobro` → `membresias_service.congelar_por_impago`)
      Nota: "POST /pagos/procesar" de plan.md no se expone como ruta HTTP real. plan.md Fase 2 dice explícitamente "no expuesto públicamente (job interno)", y el rol "sistema" no puede autenticarse (mismo motivo por el que membresias.service.ejecutar_job_renovacion tampoco tiene ruta). Se implementó como función de servicio `procesar_cobros_automaticos()`, mismo patrón ya establecido en el módulo 004.
- [X] T9 — Emitir evento "pago fallido" hacia módulo 011 (Notificaciones) en cada intento fallido
      Archivo: backend/app/modules/pagos/service.py (`_emitir_evento_pago_fallido`, stub documentado a la espera del módulo 011, mismo patrón que clases/service.py y entrenadores/service.py)
- [X] T10 — Tests de integración (incluye exclusión de membresías congeladas y congelación por impago vía endpoint de módulo 004)
      Archivo: backend/tests/modules/test_pagos.py

- [X] T11 — Numeración de factura no segura ante concurrencia:
      `_siguiente_numero_factura()` contaba filas de `Factura` dentro de la
      propia transacción del caller, así que dos operaciones concurrentes
      (dos cobros simultáneos en producción, o dos tests aislados por
      SAVEPOINT) podían calcular el mismo `numero` — visto primero como
      colisión de fichero PDF (`storage/facturas/{numero}.pdf`,
      `PermissionError` intermitente, ver specs/018 T5), pero es un bug de
      numeración de negocio, no un artefacto de tests: en producción con
      tráfico real habría producido dos facturas con el mismo `numero`.
      Fix de raíz: `numero` ahora se deriva de una SEQUENCE de Postgres
      (`factura_numero_seq`), cuyo `nextval()` es atómico y no
      transaccional — garantiza unicidad sin locking manual ni reintentos,
      y sin tocar el formato de negocio `F-{año}-{secuencial:06d}`. La
      constraint `UNIQUE` ya existente en `Factura.numero` queda como
      cinturón de seguridad, no como mecanismo primario.
      Archivo: backend/app/modules/pagos/service.py
      (`_siguiente_numero_factura`), backend/alembic/versions/
      9f3b6d2a1c47_factura_numero_seq.py
      Verificación: test nuevo `test_numeracion_factura_no_colisiona_bajo_
      concurrencia` en test_pagos.py (genera varios `numero` seguidos
      simulando la condición de carrera dentro de pytest, confirma que no
      se repiten); `tests/modules/test_pagos.py` en solitario, 30 rondas
      seguidas, 0 fallos (antes: 2 de 8 rondas fallaban con
      `PermissionError` por la colisión de `numero`)

## Conexión con módulo 004 (pendiente resuelta en esta sesión)
- `membresias/service.py::hay_pagos_pendientes` ya no es un stub: consulta `Pago.estado == "pendiente"` para la membresía dada.
- `membresias/service.py::congelar_por_impago` queda conectado como el único punto de entrada que usa `pagos/service.py::intentar_cobro` al agotar `MAX_REINTENTOS`.
