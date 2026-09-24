# Tasks 020 — Mejoras de ingeniería (revisión externa)

## Fase 1 — Barato, mucha señal

- [X] T1 — Autorización centralizada: sustituir las 5 funciones duplicadas
      (`_verificar_acceso_gestion` en `entrenadores/router.py` y
      `socios/router.py`, `_verificar_acceso_socio` en `pagos/router.py`,
      `_verificar_acceso_membresia` en `membresias/router.py`,
      `_verificar_acceso_sede` en `sedes/router.py`, `_verificar_acceso_lead`
      en `crm/router.py`) por una única `verificar_acceso_por_sede()` en
      `identidad/dependencies.py`, sin cambiar el comportamiento observable
      de ningún endpoint
      Archivos: `backend/app/modules/identidad/dependencies.py`,
      `backend/app/modules/{socios,entrenadores,pagos,sedes,crm,membresias}/router.py`
      Resultado: `membresias/router.py` conserva `_verificar_acceso_membresia`
      como envoltorio fino que delega en `verificar_acceso_por_sede` (resuelve
      el socio dueño de la membresía antes de llamar). Test nuevo en
      `backend/tests/modules/test_identidad.py` cubre
      `verificar_acceso_por_sede` de forma aislada (admin, gestor_sede con/sin
      coincidencia de sede, propietario con/sin coincidencia, y el caso sin
      `rol_propietario`). Suite completa: 268 passed, 1 failed
      (`test_socio_no_puede_editar_fecha_nacimiento`) — falla ya antes de este
      cambio (confirmado con `git stash`): `fecha_nacimiento` está en
      `CAMPOS_EDITABLES_PROPIO_SOCIO`, contradice lo que el test espera; bug
      preexistente sin relación con T1, no se toca aquí

- [X] T2 — CI/CD con GitHub Actions: workflow que corre `pytest` en cada
      push/PR contra `main`
      Archivo: `.github/workflows/`
      Resultado: `.github/workflows/ci.yml` con job `backend` (Postgres 16 de
      servicio, `pip install -r requirements.txt ruff`, `ruff check`,
      `pytest`) y job `frontend` (`npm ci`, `npm run lint`, `npm run build`).
      Badge de estado añadido al principio de `README.md`. `ruff` no se
      añadió a `requirements.txt` (solo herramienta de CI). Verificación
      local: `pip install -r requirements.txt ruff` sin error; `ruff check
      app tests` corre y encuentra 409 hallazgos preexistentes (244 B008
      function-call-in-default-argument — patrón habitual de FastAPI con
      `Depends()`, probablemente no accionable sin refactor; 48 RUF059
      unused-unpacked-variable; 43 DTZ011 + 36 DTZ003 uso de
      `date.today()`/`datetime.utcnow()` sin timezone; 17 I001 imports
      desordenados; 7 F401 imports sin usar; 6 RET501 + 6 PLR1711 returns
      innecesarios; 1 SIM102; 1 FURB157 — no corregidos, fuera de alcance de
      T2 según instrucción explícita); `npm run lint` limpio (solo 3 warnings
      preexistentes de react-hooks/react-refresh, no errores) y `npm run
      build` compila sin fallos; YAML validado con `yaml.safe_load`, sin
      errores
      Nota (remate de T2): aplicado `ruff check --fix app tests` (solo
      correcciones seguras/mecánicas — imports reordenados, imports sin usar,
      returns innecesarios; diff revisado, sin cambios de lógica) — 31 de los
      409 hallazgos corregidos. Añadido `backend/ruff.toml` con
      `ignore = ["B008"]` (falsa alarma: es el patrón `Depends(...)` de
      FastAPI, no un bug real). Quedan 128 hallazgos sin corregir, pendientes
      de revisión manual futura: 48 RUF059 (unused-unpacked-variable), 43
      DTZ011 + 36 DTZ003 (uso de `date.today()`/`datetime.utcnow()` sin
      timezone — requiere decidir si se migra a `datetime.now(tz=...)` en
      todo el módulo, no es mecánico), 1 SIM102. Verificación tras el fix:
      suite completa de pytest 268 passed, 1 failed (mismo fallo preexistente
      de `test_socio_no_puede_editar_fecha_nacimiento`, sin relación); `npm
      run lint` y `npm run build` del frontend sin cambios, ambos en verde
      CI reveló un test preexistente en rojo (`test_socio_no_puede_editar_fecha_nacimiento`) — corregido, ver specs/003/tasks.md T14.

- [X] T3 — Dockerfile básico para el backend
      Archivo: `backend/Dockerfile`
      Nota: Docker Compose (backend + Postgres + Ollama) queda aparcado en
      Fase 4 de plan.md, fuera de alcance de esta tarea — este Dockerfile
      solo empaqueta el backend, no arranca la base de datos.
      Resultado: `backend/Dockerfile` (python:3.12-slim, usuario no-root
      `appuser`) y `backend/.dockerignore`. Verificación real: `docker build
      -t gesportium-backend:test backend` construye sin errores; contenedor
      arrancado con `docker run` apuntando a Postgres del host
      (`host.docker.internal`) y las credenciales reales de `.env`;
      `curl http://localhost:8000/docs` devuelve 200; `docker logs` sin
      errores de conexión ni tracebacks, solo el arranque normal de uvicorn
      y la petición a `/docs`. Contenedor detenido tras la verificación
      (`--rm`, se autodestruye)

- [X] T13 — Fijar versión de ruff en CI (evita que un ruff nuevo rompa la
      CI sin que se toque código) + corregir los 48 RUF059
      (unused-unpacked-variable) de los 128 pendientes de T2. Los 79
      DTZ011/DTZ003 y el 1 SIM102 quedan fuera de alcance de esta tarea
      (afectan a lógica de fechas/negocio real, necesitan revisión aparte,
      no mecánica)
      Archivos: `.github/workflows/ci.yml`,
      `backend/tests/modules/{test_asistente_ia,test_entrenadores,
      test_entrenamiento,test_membresias,test_notificaciones,test_pagos}.py`
      Resultado: causa raíz confirmada por bisección de versiones —
      `backend/ruff.toml` no fija versión de ruff y el workflow tampoco
      (`pip install -r requirements.txt ruff` instala siempre la última
      disponible); entre ruff 0.15.22 y 0.16.0 el conjunto de reglas activas
      por defecto pasó de ~61 a ~414 (se activaron sin tocar config RUF059,
      DTZ011, DTZ003 y SIM102), así que el mismo código que pasaba limpio con
      0.15.22 ("All checks passed!") falla con 0.16.0 ("Found 128 errors" —
      coincide exacto con los 128 de la nota de T2). Corregido: (1)
      `.github/workflows/ci.yml` ahora instala `ruff==0.15.22` en vez de
      `ruff` a secas; (2) instalado temporalmente ruff 0.16.8 y ejecutado
      `ruff check app tests --select RUF059 --unsafe-fixes --fix`, que
      renombró las 48 variables de tuplas sin usar (p.ej. `usuario_s, socio
      = ...` → `_usuario_s, socio = ...`) en los 6 archivos de test listados
      arriba — diff revisado, solo renombrados, sin cambios de lógica.
      Verificación real: reinstalado ruff 0.15.22 (la versión fijada) →
      `ruff check app tests` → "All checks passed!"; suite completa de
      pytest con Postgres real (Docker) → 269 passed, 0 failed (mismo
      resultado que antes del cambio, los renombrados no afectan ejecución).
      Quedan pendientes 79 DTZ011/DTZ003 + 1 SIM102 (requieren revisión de
      lógica de fechas/negocio, no mecánica) — ya sin riesgo de que la CI se
      rompa sola otra vez, porque ruff queda fijado en 0.15.22

## Fase 2 — Calidad del código

- [X] T4 — Separar tests unitarios de tests de integración en
      `backend/tests/` (carpetas o markers de pytest)
      Archivo: `backend/tests/`
      Resultado: elegido markers de pytest en vez de carpetas — los 15
      archivos de `backend/tests/modules/` ya están bien organizados por
      módulo (`test_socios.py`, `test_pagos.py`, etc.) y reorganizar por
      carpetas rompería esa organización sin necesidad. Añadido
      `backend/pytest.ini` con dos markers registrados (`unit`,
      `integration`). Añadida la línea `pytestmark = pytest.mark.integration`
      cerca del principio de cada uno de los 15 archivos de
      `backend/tests/modules/` (todos los tests actuales son de integración:
      usan los fixtures `client`/`db_session`, que montan la app completa
      contra una Postgres real — todavía no existe ningún test unitario).
      Convención documentada con un comentario breve encima de esa línea en
      `test_accesos.py`, indicando que un archivo de tests unitarios nuevo
      debe llevar en su lugar `pytestmark = pytest.mark.unit`.
      Verificación real: `pytest --markers` lista los dos markers nuevos sin
      avisos de "unknown marker"; `pytest -m integration -q` → 269 passed
      (mismos tests de siempre, con Postgres real vía Docker); `pytest -m
      unit -q` → 269 deselected, 0 recogidos (confirma que el filtro
      funciona, todavía no hay tests unitarios); `pytest -q` sin filtro →
      269 passed, sin cambios de comportamiento respecto a antes; `ruff
      check app tests` → "All checks passed!"

- [ ] T5 — Añadir tests de frontend (hoy no hay ninguno)
      Archivo: `frontend/`

- [ ] T6 — Transacciones explícitas + patrón Repository: separar
      persistencia de lógica de negocio en los `service.py`, evitar
      `commit()` sueltos repartidos por los flujos
      Archivo: `backend/app/modules/*/service.py`

- [X] T14 — Definir alcance de tests unitarios: identificar qué funciones
      de los `service.py` tienen lógica de negocio real (cálculos,
      condiciones, decisiones) y proponer un plan de qué probar y cuántos
      casos por función, antes de escribir ningún test todavía
      Archivo: `backend/app/modules/*/service.py`
      Resultado: propuesta completa entregada (40 funciones candidatas,
      128 casos, priorizada en 5 tiers por riesgo real de negocio — ver
      nota íntegra debajo). Decidido no implementar las 40 de golpe: la
      implementación se aborda de forma incremental, empezando por las 2
      funciones de mayor riesgo del Tier 1 en T15
      (`_sumar_meses`/`calcular_proxima_renovacion`); el resto de la
      propuesta (resto de Tier 1 y Tiers 2-5) queda como backlog
      documentado aquí para rondas futuras, sin tarea asignada todavía.
      Nota (propuesta original, íntegra):

      Revisados los 15 `service.py` de `backend/app/modules/`. Se excluyen
      funciones que son solo `db.add()/db.commit()`/consultas simples sin
      decisiones. Lista priorizada de más a menos riesgo real de negocio:

      **Tier 1 — Cálculos financieros (mayor riesgo):**
      1. `pagos/service.py::intentar_cobro` — máquina de estados de cobro
         (pago no pendiente / cobro exitoso con factura / fallo bajo
         umbral / fallo alcanza `MAX_REINTENTOS` con membresía activa /
         fallo alcanza umbral con membresía ya no activa) — 5 casos
      2. `pagos/service.py::generar_cobro_pendiente` — evita doble cobro
         del mismo periodo (sin pago previo / pago ya existe) — 2 casos
      3. `pagos/service.py::anular_factura` / `reemitir_factura` — evita
         doble anulación o reemisión de factura viva (anular OK / anular
         ya anulada raises / reemitir anulada OK / reemitir no-anulada
         raises) — 4 casos
      4. `pagos/service.py::generar_remesa` — agregación diaria de pagos
         por sede sin duplicar remesas (dentro del día / día adyacente
         excluido / ya en otra remesa excluido) — 3 casos
      5. `membresias/service.py::_sumar_meses` — suma de meses con
         clamp de día de mes (fecha normal / 31 ene +1 mes no bisiesto /
         31 ene +1 mes bisiesto / diciembre→enero / varios meses cruzando
         año) — 5 casos
      6. `membresias/service.py::calcular_proxima_renovacion` — tabla de
         meses por duración (mensual / trimestral / anual) — 3 casos
      7. `membresias/service.py::cancelar_membresia` — bloqueo si hay
         pago pendiente + cálculo de preaviso (pago pendiente raises /
         preaviso 0 días / preaviso >0 días) — 3 casos
      8. `membresias/service.py::reactivar_membresia` — bloqueo de
         reactivación si la congelación es por impago con pago pendiente
         (sin congelación / impago con pendiente raises / impago sin
         pendiente OK / congelación voluntaria OK) — 4 casos
      9. `informes/service.py::informe_financiero` — suma ingresos vs
         impagos por estado de pago (solo exitoso / solo fallido / mezcla
         con pendiente excluido) — 3 casos

      **Tier 2 — Decisiones de acceso/seguridad:**
      10. `accesos/service.py::registrar_checkin` — decisión núcleo de
          entrada/salida (sin membresía activa raises / primer acceso
          entrada / último fue entrada→sale / último fue salida→entra) —
          4 casos
      11. `accesos/service.py::_buscar_reserva_en_curso` — ventana de
          clase para marcar asistencia automática (antes del fin / justo
          en el límite / después del fin) — 3 casos
      12. `accesos/service.py::calcular_aforo_actual` — aforo actual y
          flag de aforo superado (por debajo / justo en el máximo / por
          encima) — 3 casos
      13. `identidad/service.py::esta_bloqueado_por_intentos` — bloqueo
          por intentos fallidos en ventana de 15 min (4 fallos / 5 fallos
          dentro de ventana / 5 fallos fuera de ventana) — 3 casos
      14. `identidad/service.py::autenticar_usuario` — rechazo de login
          (email desconocido / usuario inactivo / contraseña incorrecta /
          éxito) — 4 casos
      15. `identidad/service.py::resolver_token_recuperacion` — validez
          de token de recuperación (desconocido / ya usado / expirado /
          válido) — 4 casos
      16. `identidad/service.py::decode_access_token` — validación JWT
          (token válido / inválido-expirado-manipulado) — 2 casos
      17. `entrenamiento/service.py::_validar_contenido_rutina` — puerta
          de validación entre contenido generado por IA y BD (válido /
          falta nombre / ejercicios vacío / día de semana inválido /
          campos numéricos no coercibles) — 5 casos
      18. `entrenamiento/service.py::_validar_contenido_plan_nutricional`
          — validación de plan nutricional (válido con notas / válido sin
          notas / inválido) — 3 casos

      **Tier 3 — Lógica de reservas/disponibilidad:**
      19. `clases/service.py::reservar_clase` — confirmada vs lista de
          espera según aforo (plazas libres / último asiento en el límite
          / aforo lleno) — 3 casos
      20. `clases/service.py::cancelar_reserva` — flag de cancelación
          fuera de plazo + promoción de lista de espera (bien antes de la
          ventana / dentro de la ventana / justo en el límite / cancela
          una reserva en lista de espera, sin promoción) — 4 casos
      21. `clases/service.py::calcular_ocupacion` — plazas disponibles
          con suelo en 0 (confirmadas < aforo / confirmadas >= aforo) —
          2 casos
      22. `membresias/service.py::ejecutar_job_renovacion` — selección de
          membresías a renovar por umbral de días (justo en el umbral /
          un día más allá / renovación automática desactivada) — 3 casos
      23. `membresias/service.py::ejecutar_job_vencimiento` — expiración
          de membresías no-auto-renovables (hoy no expira aún / ayer
          expirada / auto-renovación activada excluida) — 3 casos
      24. `clases/service.py::reasignar_por_baja_entrenador` —
          reasignar vs cancelar clases futuras (decisión "reasignar" /
          decisión "cancelar") — 2 casos
      25. `entrenadores/service.py::dar_baja_entrenador` — solo reasigna
          si el entrenador tiene clases futuras activas (con clases /
          sin clases) — 2 casos

      **Tier 4 — Validación de datos / decisiones de negocio (riesgo
      menor):**
      26. `crm/service.py::convertir_a_socio` — evita socio duplicado por
          usuario (usuario nuevo / usuario existente sin socio / usuario
          ya vinculado a un socio raises) — 3 casos
      27. `notificaciones/service.py::encolar_notificacion` — respeta
          opt-out solo en marketing (marketing+opt-out / marketing+opt-in
          / transaccional siempre se encola) — 3 casos
      28. `notificaciones/service.py::_procesar_envio` — reintentos antes
          de marcar fallida (éxito / fallo bajo umbral / fallo alcanza
          umbral) — 3 casos
      29. `socios/service.py::transferir_socio` — cierre/apertura de
          historial de sede (con fila abierta / sin fila abierta) —
          2 casos
      30. `informes/service.py::calcular_informe` — dispatch por tipo de
          informe (tipo válido para cada clave / tipo inválido raises) —
          2 casos

      **Tier 5 — Formateo/agregación para dashboards (menor riesgo):**
      31. `dashboard/service.py::_variacion_pct` — % de variación con
          guarda de división por cero (subida / bajada / anterior=0) —
          3 casos
      32. `dashboard/service.py::_contar_socios_activos_a_fecha` —
          reconstrucción histórica de socios activos por fecha (activo
          antes y sigue / dado de baja antes del corte / alta después del
          corte) — 3 casos
      33. `dashboard/service.py::_ocupacion_media_clases` — ocupación
          media con guarda de lista vacía (sin clases / una clase llena /
          varias clases con ocupación mixta) — 3 casos
      34. `dashboard/service.py::_tasa_conversion_leads` — tasa de
          conversión con guarda de lista vacía (sin leads / leads
          mixtos) — 2 casos
      35. `dashboard/service.py::_primer_dia_mes_siguiente` /
          `_primer_dia_mes_anterior` — aritmética de límite de mes con
          cruce de año (mes normal / límite diciembre-enero) — 2 casos
      36. `informes/service.py::informe_ocupacion` — misma lógica de
          ocupación que dashboard, debe mantenerse consistente (sin
          clases / varias clases) — 2 casos
      37. `informes/service.py::informe_comercial` — tasa de conversión
          para el periodo del informe (sin leads / leads mixtos) —
          2 casos
      38. `asistente_ia/service.py::calcular_edad` — cálculo de edad
          considerando si ya pasó el cumpleaños este año (cumpleaños ya
          pasado / cumpleaños pendiente / cumpleaños es hoy) — 3 casos
      39. `asistente_ia/service.py::generar_contenido_borrador` — rechaza
          respuesta de IA inválida (error HTTP / texto no-JSON / JSON
          válido pero no es un objeto / objeto válido) — 4 casos
      40. `entrenamiento/service.py::_normalizar_dia_semana` — normaliza
          acentos/mayúsculas de día de semana (acentuado y mayúsculas /
          minúsculas planas / ya normalizado) — 3 casos

      **Total propuesto para esta primera ronda: 40 funciones candidatas,
      128 casos de test unitarios.**

- [X] T15 — Primera ronda de tests unitarios: `_sumar_meses` y
      `calcular_proxima_renovacion` (membresias/service.py), las 2
      funciones de mayor riesgo de negocio identificadas en T14
      Archivo: `backend/app/modules/membresias/service.py`
      Resultado: creado `backend/tests/modules/test_membresias_unitarios.py`
      con `pytestmark = pytest.mark.unit` (convención de T4), sin
      fixtures `client`/`db_session` — llama a las funciones directamente,
      sin base de datos ni HTTP. Leído el código real antes de escribir
      los tests: `_sumar_meses(fecha, meses)` calcula el mes/año destino y
      usa `min(fecha.day, calendar.monthrange(anio, mes)[1])` para
      acotar el día al último día válido del mes destino (no hace
      "overflow" a marzo). `calcular_proxima_renovacion(fecha_inicio,
      duracion)` mira `MESES_POR_DURACION[duracion]` (dict plano, sin
      `.get()`, así que una duración desconocida lanza `KeyError`) y
      delega en `_sumar_meses`. Tests para `_sumar_meses`: caso normal
      (15 marzo + 1 mes), fin de mes en año no bisiesto (31 enero + 1 mes
      → 28 febrero), fin de mes en año bisiesto (31 enero + 1 mes → 29
      febrero), cruce de año (5 diciembre + 1 mes → 5 enero siguiente).
      Tests para `calcular_proxima_renovacion`: mensual, trimestral,
      anual, fin de mes bisiesto propagado desde `_sumar_meses`, y
      duración inválida (`KeyError`). 9 tests en total. No se ha tocado
      ninguna de las otras 38 funciones del backlog de T14.
      Verificación real: `pytest -m unit -q` → 9 passed, 269 deselected
      (antes 0 recogidos); `pytest -m integration -q` → 269 passed, 9
      deselected (sin cambios); `pytest -q` sin filtro → 278 passed
      (269 + 9 nuevos, sin regresiones); `ruff check app tests` → "All
      checks passed!"

- [X] T16 — Validación explícita de `duracion` inválida en
      `calcular_proxima_renovacion` (sustituir el `KeyError` sin
      controlar detectado en T15 por un error de negocio claro)
      Archivo: `backend/app/modules/membresias/service.py`
      Resultado: seguido el mismo patrón ya usado en este módulo
      (`reactivar_membresia`, `cancelar_membresia`: `raise ValueError(...)`
      en el service, capturado en el router con
      `except ValueError as exc: raise HTTPException(...)`).
      `calcular_proxima_renovacion` ahora comprueba
      `if duracion not in MESES_POR_DURACION` ANTES de acceder al
      diccionario y lanza `ValueError(f"Duración de membresía no válida:
      '{duracion}'")` en vez de dejar que falle por accidente con un
      `KeyError`. En la práctica esta función solo se invoca hoy con
      `plan.duracion`, que ya está validado como `Literal["mensual",
      "trimestral", "anual"]` en `PlanMembresiaCreate` (pydantic) — así que
      una `duracion` inválida no puede llegar hoy vía la API — pero se
      añade igualmente como red de seguridad explícita en el service (y no
      solo implícita vía el tipo de Pydantic), y por defensa en
      profundidad se envuelve también la llamada a `service.crear_membresia`
      en `POST /membresias` (`membresias/router.py`) en un
      `try/except ValueError` que devuelve 422 Unprocessable Entity (se
      eligió 422 en vez de 409 porque es un dato inválido, no un conflicto
      de estado — a diferencia de `reactivar_membresia`/`cancelar_membresia`,
      que sí son conflictos de estado y ya usan 409).
      Test de T15 actualizado: `test_duracion_invalida_lanza_keyerror` →
      renombrado a `test_duracion_invalida_lanza_valueerror_con_mensaje_claro`,
      ahora comprueba `pytest.raises(ValueError, match=...)` con el mensaje
      exacto en vez de `KeyError`. Mismo número de tests (9), no se ha
      añadido ningún caso nuevo.
      Verificación real: `pytest -m unit -q` → 9 passed (mismo número que
      T15, el test de duración inválida ahora comprueba el nuevo
      comportamiento); `pytest -q` sin filtro → 278 passed, sin
      regresiones; `ruff check app tests` → "All checks passed!"

## Fase 3 — Estructura y documentación

- [ ] T7 — Reorganizar backend/frontend por dominio en vez de por capa
      técnica
      Archivo: `backend/app/`, `frontend/src/`

- [ ] T8 — `AGENTS.md` en la raíz del repo + ordenar qué es config de
      Speckit (`.specify/`) y qué es código de producto
      Archivo: `AGENTS.md`

- [ ] T9 — Logging / reporte de errores estructurado
      Archivo: `backend/app/core/`

## Fase 4 — Aparcado, sin prisa (referencia, no implementar sin encargo explícito)

- [ ] T10 — Sistema de permisos configurable por usuario/rol desde una
      pantalla (feature de producto aparte, no forma parte de T1)

- [ ] T11 — Explorar si algún MCP tiene sentido (sin caso de uso concreto
      todavía)

- [ ] T12 — Docker Compose completo (backend+Postgres+Ollama con
      healthchecks) y notificaciones asíncronas con RabbitMQ
