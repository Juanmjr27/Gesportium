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

## Fase 2 — Calidad del código

- [ ] T4 — Separar tests unitarios de tests de integración en
      `backend/tests/` (carpetas o markers de pytest)
      Archivo: `backend/tests/`

- [ ] T5 — Añadir tests de frontend (hoy no hay ninguno)
      Archivo: `frontend/`

- [ ] T6 — Transacciones explícitas + patrón Repository: separar
      persistencia de lógica de negocio en los `service.py`, evitar
      `commit()` sueltos repartidos por los flujos
      Archivo: `backend/app/modules/*/service.py`

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
