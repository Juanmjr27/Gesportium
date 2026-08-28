# Changelog

## 2026-08-28 — Control de versiones del proyecto completo (specs/019)

Hallazgo colateral, del mismo tipo que specs/018: al comitear los fixes de
007/T10 y 003/T13 se confirmó que el repositorio se había inicializado en
algún momento con un `git init` que solo llegó a comitear `LICENSE`
(`cfea2fb`, "Initial commit"). `backend/` se trackeó aparte en esta misma
sesión como línea base (`cb00815`, previa al fix de specs/018), pero el
resto del proyecto — `frontend/` completo (incluido el código ya dado por
"hecho" de todos los módulos, p. ej. el wizard de 016), el historial de
specs de 001 a 017, `bocetos/` y `roadmap/` — llevaba sin ninguna
protección de control de versiones desde el inicio del proyecto.

Investigación previa al commit (specs/019, plan.md):
- **`.gitignore` de raíz**: ya cubría Python/venv/`.env`/`backend/
  storage/`, pero nada de frontend. `frontend/.gitignore` (scaffold
  estándar de Vite) ya excluía `node_modules/`/`dist/` por precedencia de
  git sobre `.gitignore` anidados, pero se añadió también una sección
  `frontend/` explícita al `.gitignore` de raíz para que sea por sí solo
  una referencia completa. Confirmado que no hay ningún `.env`/`.env.
  local` en frontend (el cliente no usa variables de entorno). Excluidas
  también dos capturas de debug sueltas encontradas en `frontend/`
  (`t13-debug.png`, `t13-wizard-paso1.png`), residuo de una sesión de
  verificación manual del wizard de 016, sin relación con el código
  fuente.
- **`.claude/` y `.specify/`**: decidido fichero por fichero, no en
  bloque. `.claude/skills/` (plantillas de los comandos `/speckit-*`) y el
  resto de `.specify/` (scripts, templates, workflows, `memory/
  constitution.md`, `integration.json`, `integrations/*.manifest.json`,
  `init-options.json`) son config limpia del framework spec-kit del
  proyecto, sin datos personales: se trackean. `.claude/settings.json` y
  `.claude/settings.local.json` resultaron ser, en la práctica, el mismo
  tipo de contenido — listas acumuladas de comandos auto-aprobados con
  rutas absolutas de esta máquina; `settings.local.json` además tenía un
  JWT de sesión pegado en texto plano (token de prueba usado contra
  `localhost:8000`). `.specify/feature.json` es un puntero de una sola
  línea al feature activo, reescrito en cada sesión por los scripts de
  `speckit` — estado de sesión local, no config del proyecto. Los tres se
  excluyeron explícitamente vía `.gitignore`, decisión confirmada por el
  usuario antes de continuar.
- **Escaneo de secretos**: `grep` amplio (claves de API, contraseñas,
  tokens, `-----BEGIN`, JWT literales) sobre todo lo que se iba a añadir
  (`frontend/src`, config de frontend, `specs/001` a `specs/017`,
  `roadmap/`, ficheros de texto de `bocetos/`). Sin hallazgos reales:
  todas las coincidencias eran nombres de variable/campo legítimos del
  propio código o menciones de diseño en los specs (cómo se firma un JWT,
  no el secreto en sí). Ningún `.env` fuera de `backend/` (ya cubierto
  desde `cb00815`).

Verificación previa al commit: `git status --short` completo en la raíz
tras el `git add` (no un `git add -A` a ciegas), y `git diff --cached
--name-only | grep -iE "node_modules|dist/|settings.*json|feature.json|
t13-debug|t13-wizard"` sin resultados, confirmando que ninguno de los
ficheros excluidos se coló en el commit.

Archivos: `.gitignore` (actualizado), `frontend/` completo,
`specs/001 - Identidad y Roles/` a `specs/017 - Panel de administración/`,
`bocetos/`, `roadmap/`, `.claude/skills/`, `.specify/` (salvo
`feature.json`). Task: `specs/019 - Control de versiones del proyecto
completo/tasks.md`.

## 2026-08-27 — Numeración de factura no segura ante concurrencia (specs/008 T11)

Corregido de raíz el bug confirmado el 2026-08-26 (specs/018 T5,
"Confirmación empírica"): `_siguiente_numero_factura()`
(`backend/app/modules/pagos/service.py`) calculaba el `numero` de factura
contando filas de `Factura` **dentro de la propia transacción** del
caller, así que dos transacciones concurrentes (dos cobros simultáneos en
producción, o dos tests aislados por SAVEPOINT) podían calcular el mismo
secuencial. En tests esto se manifestaba como colisión de fichero PDF
(`storage/facturas/{numero}.pdf`, `PermissionError` intermitente en
Windows); en producción con tráfico real habría sido un bug de negocio —
dos facturas emitidas con el mismo número.

Fix: `numero` ahora se deriva de una SEQUENCE de Postgres
(`factura_numero_seq`, migración
`backend/alembic/versions/9f3b6d2a1c47_factura_numero_seq.py`). `nextval()`
es atómico y no transaccional (no se ve afectado por rollback ni por el
punto de partida de la transacción del caller), así que garantiza
unicidad real bajo concurrencia sin necesidad de locking manual
(`SELECT ... FOR UPDATE`) ni reintentos ante colisión — se descartó ese
enfoque por ser más código para el mismo resultado, dado que Postgres ya
ofrece la primitiva correcta. El formato de negocio
`F-{año}-{secuencial:06d}` no cambia; la constraint `UNIQUE` ya existente
en `Factura.numero` queda como cinturón de seguridad, no como mecanismo
primario de unicidad.

Verificación: test nuevo
`test_numeracion_factura_no_colisiona_bajo_concurrencia`
(`backend/tests/modules/test_pagos.py`) — 10 hilos con conexiones y
transacciones independientes, sincronizados con una barrera para forzar
el solape real que antes producía la colisión, confirma `numero` únicos.
Además, `tests/modules/test_pagos.py` en solitario, **30 rondas seguidas,
0 fallos** (antes del fix: 2 de 8 rondas fallaban con `PermissionError`
por la colisión de `numero`, ver specs/018 T5). Con esto, el hallazgo
colateral de specs/018 queda cerrado y quitado de "Pendientes" (ver más
abajo).

Archivos: `backend/app/modules/pagos/service.py`,
`backend/alembic/versions/9f3b6d2a1c47_factura_numero_seq.py`,
`backend/tests/modules/test_pagos.py`. Task:
`specs/008 - Pagos y facturación/tasks.md` T11.

## 2026-08-26 — Aislamiento de entorno de tests (specs/018) + fixes de módulos 007/003 detectados en verificación de 016

Housekeeping previo (bloqueaba el resto): `backend/` estaba sin trackear en
git desde el "Initial commit" (solo incluía `LICENSE`). Añadido y commiteado
tal cual estaba, junto con el `.gitignore` raíz (también sin trackear, ya
cubría `venv/`/`__pycache__/`/`.env` correctamente — no hizo falta tocarlo),
como línea base antes de tocar nada más.

Dos bugs de otros módulos, detectados durante la verificación manual de
016/T21 y ya reportados sin arreglar, corregidos en esta sesión:

**Módulo 007 (T10)** — `_validar_contenido_rutina()`
(`backend/app/modules/entrenamiento/service.py`) rechazaba `dia_semana` con
tilde (p. ej. "miércoles") porque comparaba directo contra `DIAS_SEMANA`
(sin tildes), y Ollama genera los nombres de día acentuados — bug ya visto
dos veces (016/T19 y T21). Corregido con `_normalizar_dia_semana()`
(minúsculas + sin tildes vía `unicodedata`), aplicada antes de comparar y de
guardar, en vez de añadir variantes acentuadas a mano una por una. Verificado
con test nuevo (rutina con "miércoles" y "Sábado" mezclados).

**Módulo 003 (T13)** — `SocioUpdate` (`backend/app/modules/socios/
schemas.py`) declaraba sus 5 campos como opcionales para permitir update
parcial, pero las columnas correspondientes son NOT NULL en BD: un
`PUT /socios/{id}` con, p. ej., `fecha_nacimiento: null` explícito pasaba la
validación de Pydantic y reventaba en la BD con un 500 en vez de un 422.
Corregido con un `model_validator(mode="after")` que usa `model_fields_set`
para distinguir "campo omitido" (sigue permitiendo update parcial) de "campo
enviado como null" (ahora rechazado con 422), sin quitar `Optional` de los
campos. Verificado con 2 tests nuevos y en vivo contra el backend real
(422/200/200 para los tres casos). Nota: el caso borde de 016/T14 (socio con
`fecha_nacimiento` genuinamente faltante) sigue siendo inalcanzable por vía
legítima — igual que se documentó en T21 —, ya que el alta (`SocioCreate`)
sigue exigiendo el campo; este fix solo convierte el 500 erróneo en un 422
correcto ante un intento inválido, no habilita una vía nueva para llegar a
ese estado.

**specs/018 (nuevo módulo) — aislamiento pytest↔servidor real.** Verificando
el fix de T13 salió un tercer bug, de infraestructura: `pytest` y el
servidor de desarrollo (`uvicorn`) compartían la misma base de datos
PostgreSQL. `db_session` (`backend/tests/conftest.py`) aísla cada test de
otro test (SAVEPOINT + rollback), pero no aísla la suite de lo que el
servidor real haya comprometido en paralelo (verificaciones manuales con
Playwright, `verify_bugs.mjs` y similares contra `localhost:8000`) — ya
había pasado dos veces (016/T10, y de nuevo verificando 003/T13, con 24
filas sueltas de `BorradorIA`).

Corregido: BD de test separada, misma instancia PostgreSQL (sin SQLite ni
mocks del motor, por paridad con el resto del proyecto). Resuelta vía
`TEST_DATABASE_URL` (opcional, nueva en `.env.example`) o, por defecto,
`DATABASE_URL` con `_test` añadido al nombre de la base
(`gesportium`→`gesportium_test`); se crea sola si no existe (requiere
`CREATEDB`, confirmado disponible) y se construye con `alembic upgrade
head` — no `Base.metadata.create_all()` — para incluir también los datos
sembrados por migraciones de datos (`configuracion_global`, migración
`deb0740ca027`), que `create_all()` no ejecuta. `backend/app/core/
config.py` gana `test_database_url: str | None = None`.

Limpieza de la BD de desarrollo: 29 usuarios de un solo uso dejados por
sesiones de verificación anteriores (`ia-t21-socio-*`, `verify-bugs-*`,
`t14wizard@test.com`, etc.) y todo lo que dependía de ellos en cascada (23
de las 24 filas de `BorradorIA`, socios, entrenadores, rutinas, planes
nutricionales, asignaciones, notificaciones, historial, clases), con un
script puntual que recorre el grafo de FKs de `Base.metadata` en vez de una
lista de tablas mantenida a mano. Se conservó la cuenta de humo estable
(`smoke-admin@test.com`/`smoke-entrenador@test.com`/`smoke-socio@test.com`,
reutilizada a propósito entre sesiones) y su fila de `BorradorIA`.

Verificado (criterio de aceptación de specs/018): suite completa dos veces
seguidas, y una vez más justo después de una sesión de verificación manual
real contra `localhost:8000` de por medio — mismo resultado exacto las tres
veces (261 passed / 1 failed; el único fallo,
`test_socios.py::test_socio_no_puede_editar_fecha_nacimiento`, es un test
desactualizado sin relación, ya confirmado en sesiones anteriores).

Hallazgo colateral, documentado pero no corregido aquí (fuera del alcance
de specs/018): un tercer run de control mostró además
`test_pagos.py::test_socio_descarga_su_propia_factura` en rojo — no
relacionado con la contaminación cruzada pytest↔servidor real (confirmado:
`test_pagos.py` en solitario pasa 3/3 de forma estable en ese momento).
Causa raíz: `_siguiente_numero_factura()` numera facturas contando filas de
`Factura` dentro de la propia transacción del test; como cada test empieza
con la tabla vacía, varios tests que emiten su primera factura calculan el
mismo `numero`, y el PDF se escribe a `storage/facturas/{numero}.pdf` —
mismo nombre de fichero en disco entre tests distintos, fuera de la
transacción de BD y por tanto no cubierto por el rollback de `db_session`,
produciendo fallos intermitentes en Windows por bloqueo de fichero.

**Actualización 2026-08-26 (post-entrega):** reproducido de forma
controlada — `test_pagos.py` en solitario, 8 runs seguidos, falló 2/8 con
`PermissionError` al reescribir `storage/facturas/F-2026-000001.pdf` (el
mismo test aislado pasa 6/6). Confirma que es un bug real e intermitente
por sí mismo, no una casualidad del run de control ni un efecto del cambio
de BD de test — y no afecta al criterio de aceptación de specs/018 (que es
específicamente sobre la BD compartida pytest↔servidor real, ya resuelto y
verificado aparte). Ver
`specs/018 - Aislamiento de entorno de tests/tasks.md` (T5) para el
diagnóstico completo, la reproducción y la recomendación de fix.

## 2026-08-24 — Backend del asistente IA conversacional: cuestionario guiado y revisión del entrenador (specs/016)
Ampliada la spec 016: el formulario de "Solicitar un borrador" (solo tipo +
objetivo libre) se sustituye por un cuestionario guiado paso a paso, y el
entrenador pasa a ver los datos estructurados del socio junto al borrador
generado, no solo el borrador a ciegas. Esta entrada cubre el backend
completo (T1-T11 de tasks.md); el frontend (wizard de 5 pasos y panel de
revisión del entrenador) queda pendiente en T13-T21.
 
Cambiado en `backend/app/modules/asistente_ia/models.py`: `borradores_ia`
gana `datos_cuestionario` (JSONB, NOT NULL — respuestas completas del
wizard) y `motivo_rechazo` (Text, nullable); `TIPOS_BORRADOR` renombra
`nutricion` a `plan_nutricional`. Migración `5fe144b91322`
(`down_revision = "2abd213f134d"`) añade ambas columnas —
`datos_cuestionario` con `server_default="{}"` temporal para no romper
filas ya existentes, retirado tras el `add_column` — y migra los valores de
`tipo` ya guardados. Aplicada con `alembic upgrade head` (confirmado con
`alembic heads` → `5fe144b91322 (head)`).
 
Cambiado en `schemas.py`: `BorradorCreate` se sustituye por
`WizardBorradorRequest`, con todos los campos del cuestionario (peso_kg,
altura_cm, nivel_actividad_actual/restricciones_medicas,
dias_disponibles_semana/preferencia_alimentaria,
equipamiento/comidas_al_dia, objetivo_principal, objetivo_detalle),
validaciones de rango (peso_kg 20-300, altura_cm 100-250,
dias_disponibles_semana 1-7, comidas_al_dia 2-6, objetivo_detalle máx. 280
caracteres) y un `model_validator` que exige los campos propios de
`tipo_borrador` (rutina vs. plan_nutricional). `BorradorOut` expone ahora
`datos_cuestionario` y `motivo_rechazo`. Nuevos `BorradorEditar` (body del
PATCH) y `BorradorRechazar` (`motivo` obligatorio).
 
Cambiado en `router.py`/`service.py`: `POST /asistente/borrador` acepta el
payload completo del wizard y guarda `datos_cuestionario` aparte de
`contenido`; `service.generar_contenido_borrador()` cambia de firma —recibe
el dict completo del cuestionario en vez de un `objetivo` suelto— y arma un
prompt para Ollama con todas las respuestas, no solo el objetivo.
`GET /asistente/borradores-pendientes` no requirió cambio de código: al
exponer `BorradorOut` ya devuelve `datos_cuestionario` junto a `contenido`
en la misma respuesta. Nuevo endpoint `PATCH /asistente/borradores/{id}`
(entrenador, solo sobre borradores pendientes de sus socios asignados):
edita `contenido` sin cambiar `estado`, habilitando el flujo "editar y
aprobar" de la spec. `POST /asistente/borradores/{id}/rechazar` ahora exige
`motivo` en el body y lo persiste en `motivo_rechazo`. `aprobar` no cambió
(usa `contenido`, ya editado si se llamó antes al PATCH).
 
Rotura y arreglo urgente de frontend: estos cambios de contrato rompieron
`AsistentePage.jsx` y `BorradoresPendientesPage.jsx`, que ya estaban en
producción llamando al `BorradorCreate` y al `/rechazar` sin body
anteriores (ver entrada 2026-08-23). Se aplicó un arreglo mínimo (T12): un
formulario plano en `AsistentePage.jsx` con todos los campos nuevos del
wizard (todavía no el wizard de 5 pasos) y una textarea de `motivo`
obligatoria antes de rechazar en `BorradoresPendientesPage.jsx`, más el
rename de `nutricion` a `plan_nutricional` en las etiquetas de ambas
páginas. Verificado en vivo contra el backend real:
`POST /asistente/borrador` devuelve 201 (no 422) para rutina y
plan_nutricional con el payload nuevo, y `POST .../rechazar` devuelve 200
(no 422) con motivo, retirando el borrador rechazado de la lista de
pendientes sin afectar al resto. `npm run build` y `npm run lint` limpios.
 
Verificado (T10): `test_asistente_ia.py` actualizado al contrato nuevo —
payloads completos válidos (rutina y plan_nutricional), 422 al faltar
campos condicionados por `tipo_borrador`, validación de rangos
parametrizada, persistencia y exposición de `datos_cuestionario`, `PATCH`
(solo sobre pendientes, solo del propio socio asignado, 403/409 en el
resto de casos), `rechazar` exige `motivo` y lo persiste, `aprobar` sigue
funcionando para ambos tipos. 35/35 tests en `test_asistente_ia.py`; suite
completa 255/259 (4 fallos preexistentes no relacionados con este cambio:
una aserción de `test_informes.py` dependiente de la fecha del calendario y
filas huérfanas en `test_notificaciones.py` de ejecuciones anteriores no
relacionadas).
 
Bug encontrado y corregido durante T10: los helpers `_crear_borrador` de
`test_asistente_ia.py` y `test_entrenamiento.py` eran anteriores a la
migración `5fe144b91322` y no rellenaban la nueva columna NOT NULL
`datos_cuestionario`, lo que rompía los `INSERT` con `IntegrityError` y de
paso corrompía el rollback transaccional compartido entre tests,
filtrando ~16-18 filas huérfanas a la base de datos real de desarrollo en
dos tablas — limpiado directamente en Postgres.

## 2026-08-23 — Frontend del asistente IA conversacional (specs/016)
El backend de 016 ya estaba completo y probado desde una sesión anterior
(6 endpoints, integración real con Ollama); no existía ningún frontend.
Añadido en esta sesión: chat del socio y revisión de borradores del
entrenador, sin tocar backend.

Investigación previa a implementar (spec.md menciona "edad, objetivo,
membresía" como input de la IA para un borrador, pero "objetivo" no está
definido en ningún otro sitio del proyecto): revisando
`backend/app/modules/asistente_ia/router.py`/`service.py` se confirmó que
"edad" y "membresía" los calcula el propio backend a partir de
`Socio.fecha_nacimiento` y la `Membresia` activa, pero `objetivo` es un
campo de texto libre que espera literalmente en el body de
`POST /asistente/borrador` (`BorradorCreate.objetivo`, requerido) — no se
obtiene de ningún campo existente del socio. Por tanto el frontend pide
este dato en un formulario antes de generar el borrador, en vez de
inferirlo.

Portal de socio: nueva página `frontend/src/portal-socio/pages/AsistentePage.jsx`
en `/asistente` (enlazada en el menú de `AppShell.jsx`). Chat con historial
(`GET /asistente/historial`) y envío (`POST /asistente/mensaje`); formulario
para solicitar un borrador de rutina o plan nutricional (selector de tipo +
campo de texto libre "objetivo") que llama a `POST /asistente/borrador`.
Todo borrador con `estado === 'pendiente'` muestra siempre el aviso
obligatorio "Esto es un borrador generado por IA, pendiente de revisión
profesional." Un 503 de Ollama (tanto en el chat como al pedir un borrador)
se captura y muestra como mensaje de error inline sin romper el resto de la
página.

Panel admin (vista de entrenador): nueva página
`frontend/src/panel-admin/pages/BorradoresPendientesPage.jsx` en
`/admin/borradores-ia`, restringida a rol `entrenador` (única ruta gateada
así en `App.jsx`, coherente con que el propio endpoint de backend solo
acepta ese rol) y enlazada en `AdminShell.jsx` solo para ese rol. Lista los
borradores pendientes de los socios asignados
(`GET /asistente/borradores-pendientes`), cruzados con
`sociosService.listarSocios()` para mostrar el email del socio (con enlace a
su ficha). Aprobar/rechazar llaman a
`POST /asistente/borradores/{id}/aprobar|rechazar` (ya implementados en el
backend; aprobar reutiliza `entrenamiento_service.crear_rutina_desde_borrador`/
`crear_plan_nutricional_desde_borrador` tal cual, sin duplicar lógica).

Bug encontrado y corregido durante la prueba manual: el mensaje de error de
un 503 estaba hardcodeado en un único texto compartido
(`mensajeErrorApi` en `AsistentePage.jsx`), así que un fallo de Ollama al
pedir un borrador mostraba el texto genérico del chat ("El asistente no
está disponible...") en vez de uno específico de borradores. Se corrigió
para aceptar un mensaje de 503 específico por caso de uso.

Verificación: `npm run build` y `npm run lint` limpios (solo warnings
preexistentes no relacionados); 17/17 tests de
`backend/tests/modules/test_asistente_ia.py` en verde antes de generar
tráfico real contra el backend de desarrollo (nota: tras las pruebas E2E
manuales con Ollama y mensajes/borradores reales, 3 de esos tests fallan
porque hacen aserciones sin scope sobre el total de filas de la tabla
—`db_session.query(MensajeIA).all()`— y esa base de datos es la misma que
usa el backend de desarrollo, no una aislada; es una fragilidad
preexistente del test, no una regresión de este cambio — confirmado
volviendo a correr esos tests limpios, 17/17, antes de tocar el backend
real). Prueba manual real en navegador (Playwright, dos roles, backend y
Ollama reales):
- Como socio: mensaje de chat con respuesta real del asistente; simulación
  de fallo 503 del chat (interceptando la red) mostrando el error sin
  romper la página; solicitud de un borrador de rutina y de un plan
  nutricional (ambos generados de verdad por Ollama), mostrando en ambos el
  aviso obligatorio; simulación de fallo 503 al pedir un borrador mostrando
  el error específico corregido arriba.
- Como entrenador: ambos borradores visibles en "Borradores IA pendientes"
  con el email del socio correcto; aprobado el de rutina (se creó la rutina
  real, visible en la ficha del socio con sus ejercicios) y rechazado el de
  plan nutricional (la ficha del socio siguió mostrando "Sin planes
  nutricionales registrados", confirmando que rechazar no crea nada).
- Como socio de nuevo: la rutina aprobada apareció en "Mi Entrenamiento"
  con sus ejercicios reales, confirmado tanto en la respuesta real de
  `GET /rutinas/{socioId}` como visualmente en la UI.

## 2026-08-23 — Panel admin: dashboard del entrenador (bug + contadores)
Bug corregido: las tarjetas "Mis socios" y "Mis clases" del dashboard del
entrenador (`frontend/src/panel-admin/pages/DashboardPage.jsx`) usaban
`<a href="...">`, lo que provocaba una recarga completa de página. Como la
sesión del panel admin vive solo en estado de React (sin `localStorage`,
confirmado en `useAuth.jsx`), la recarga perdía el token y redirigía a
login — pese a que las mismas páginas cargaban bien desde el menú lateral
(que sí usa navegación interna del router). Corregido cambiando ambos
enlaces a `<Link>` de `react-router-dom`.
Mejora: cada tarjeta ahora muestra un contador real además de servir de
acceso directo. "Mis socios" reutiliza `sociosService.listarSocios()` (el
listado ya viene filtrado a los asignados del entrenador por el backend
existente, sin endpoint nuevo) y cuenta el total. "Mis clases" reutiliza
`clasesService.listarClases()` (igualmente ya filtrado por entrenador en
`GET /clases`) y cuenta, en el cliente, las clases con `estado === 'activa'`
cuya `fecha_hora` cae dentro de la semana en curso (lunes 00:00 a domingo
24:00); no se tocó el backend de 007/017 ni se añadió ningún parámetro
nuevo a `/clases`.
Verificación: `npm run build` y `npm run lint` limpios (solo warnings
preexistentes no relacionados). Prueba manual real en navegador (Playwright)
logueado como entrenador con 2 socios asignados y 3 clases de prueba (2 en
la semana actual, 1 en la siguiente): las tarjetas mostraron "2 socios
asignados" y "2 clases esta semana" (excluyendo correctamente la de la
semana siguiente), y el clic en cada tarjeta navegó a `/admin/socios` y
`/admin/clases` respectivamente sin perder la sesión (sin redirección a
login, confirmado por ausencia de los campos de login tras la navegación).

## 2026-08-22 — Panel admin: ficha de socio (specs/017 FR8)
Añadido: pantalla de detalle de un socio (`/admin/socios/:socioId`), accesible
haciendo clic en cualquier fila de la tabla de Socios (`DataTable` gana un
prop opcional `onRowClick`, sin romper a sus otros consumidores). Implementa
FR8 de `specs/017 - Panel de administración/spec.md`, añadido en una sesión
anterior como formalización de un hueco detectado en auditoría (la ficha no
existía en ningún spec pese a ser el destino natural de "crear rutina/plan
para un socio concreto").
Backend: nuevo endpoint `GET /socios/{socio_id}/ficha`
(`backend/app/modules/socios/router.py`), gateado a
`admin`/`gestor_sede`/`entrenador`. Es un agregador puro: reutiliza modelos y
schemas ya existentes de 004 (`Membresia`/`MembresiaDetail`), 006
(`SocioAsignado`/`Entrenador`) y 007 (`Rutina`/`PlanNutricional`/`RutinaOut`/
`PlanNutricionalOut`) sin duplicar su lógica de negocio — no se tocó ningún
endpoint ni servicio de esos módulos. Nunca incluye `NotaSocio` (notas
internas): el schema `SocioFichaOut` simplemente no tiene ese campo, mismo
criterio que `SocioSelf`. Permisos: admin ve cualquier socio; gestor_sede solo
los de su sede (`_verificar_acceso_gestion`, reutilizado); entrenador solo
los que tiene asignados (`entrenadores_service.ids_socios_asignados`,
reutilizado de 006) — 403 en cualquier otro caso.
Frontend: `frontend/src/panel-admin/pages/FichaSocioPage.jsx` (nueva).
Admin/gestor_sede ven todo en modo consulta (datos personales, sede, estado,
membresía, entrenador asignado, rutinas y planes nutricionales). Entrenador
ve lo mismo y además puede crear y editar rutinas/planes nutricionales del
socio abierto, reutilizando tal cual los endpoints de 007
(`POST/PUT /rutinas`, `POST/PUT /planes-nutricionales` — no se creó ningún
endpoint de escritura nuevo); el formulario de edición de rutina se limita a
nombre/activa porque es lo único que `RutinaUpdate` permite (no hay endpoint
para editar ejercicios). Nuevo servicio
`frontend/src/panel-admin/services/entrenamientoService.js` (no existía en el
panel admin, solo en el portal de socio) y `sociosService.obtenerFichaSocio`.
Ningún rol puede dar de baja ni transferir de sede desde esta pantalla (esas
acciones siguen solo en la tabla de Socios, sin cambios).
Bug encontrado y corregido durante la prueba manual: al navegar de la ficha
de un socio a la de otro (mismo componente de ruta reutilizado por React
Router al cambiar solo el parámetro `:socioId`), si la nueva petición fallaba
(403), la ficha del socio anterior se quedaba visible en pantalla en vez de
limpiarse — el `useEffect` ahora resetea `ficha`/`error` a su estado inicial
en cada cambio de `socioId`, antes de lanzar la nueva petición.
Verificado: 24/24 tests de `test_socios.py` en verde (4 nuevos: admin ve
ficha completa sin notas; gestor_sede no puede ver ficha de otra sede;
entrenador ve ficha de socio asignado sin notas; entrenador no puede ver
ficha de socio no asignado). Resto de la suite backend en verde salvo los 3
fallos intermitentes ya documentados (`test_informes`, `test_notificaciones`,
`test_pagos::test_socio_descarga_su_propia_factura`), no relacionados con
este cambio. `npm run build` y `npm run lint` sin errores nuevos. Prueba
manual en navegador (Playwright contra los servidores de desarrollo reales)
con los tres roles: admin abre la ficha de un socio y la ve en solo lectura
(sin botones "Nueva rutina"/"Nuevo plan"/"Editar"); entrenador abre la ficha
de su socio asignado, crea una rutina y un plan nutricional nuevos y los ve
aparecer; entrenador no ve al socio no asignado en el listado de Socios y,
al forzar la URL directamente, recibe un error controlado sin filtrar ningún
dato del socio (403 del backend, sin ficha previa residual tras el fix del
bug anterior).

## 2026-08-22 — Panel admin: alta directa de entrenador (email + contraseña), corrige el enfoque anterior
Corregido: la entrada anterior de este mismo día ("alta de entrenador por
email en vez de UUID") aplicó al modal "Nuevo Entrenador" el patrón de
"buscador de candidatos ya registrados" copiado de "Alta de Socio"
(`GET /entrenadores/candidatos-alta`). Ese enfoque no encajaba: un socio se
autorregistra en el portal público y luego un gestor lo asocia a una
membresía, pero un entrenador es personal del gimnasio — no existe (ni debe
existir) un registro público previo para ese rol. El resultado práctico era
que el admin tenía que crear la cuenta del entrenador por otra vía (API) antes
de poder "encontrarlo" en el buscador, un paso intermedio innecesario.
Cambiado: el modal "Nuevo Entrenador" pasa a dar de alta en un único envío:
email, contraseña (introducida directamente por el admin, sin autogenerar),
sede y especialidades. `POST /entrenadores` ahora crea en la misma
transacción la cuenta de usuario (rol "entrenador", reutilizando
`identidad_service.crear_usuario`, las mismas reglas de contraseña que ya
regían el registro — mínimo 8 caracteres) y el perfil `Entrenador` enlazado a
esa cuenta. Devuelve 409 con mensaje claro si el email ya está registrado.
Eliminado (código muerto tras el cambio de enfoque): endpoint
`GET /entrenadores/candidatos-alta` y su schema `CandidatoEntrenadorOut`
(backend), el buscador con autocompletado y sus 3 tests (frontend/backend).
Verificado: tests backend (alta con email nuevo crea cuenta + perfil y
permite login; email duplicado devuelve 409 con mensaje claro); resto de la
suite en verde salvo los fallos intermitentes ya documentados (más uno nuevo
observado hoy, `test_pagos.py::test_cobro_exitoso_audita_pago_y_factura`,
que también pasa en aislado — dependencia de orden de ejecución entre tests,
no relacionado con este cambio). Prueba manual en navegador (Playwright
contra los servidores de desarrollo reales): admin crea un entrenador desde
el modal, aparece en la tabla, cierra sesión, inicia sesión con la cuenta
nueva y accede al panel con la vista de entrenador (nav restringida a
Dashboard/Socios/Clases, etiqueta de rol "Entrenador" en la cabecera).

## 2026-08-19 — Portal de socio: histórico de clases limitado a la semana actual y texto de botón corregido
Cambiado (módulo 005/015): el catálogo de clases del portal de socio ya no
mostraba indefinidamente las clases pasadas sobre las que el socio tenía una
reserva. Ahora ese histórico se limita a la semana en curso (lunes-domingo,
convención España): una clase pasada con reserva sigue visible solo hasta el
domingo a las 00:00 (el instante en que pasa a ser lunes); a partir de ahí
las clases de la semana anterior dejan de aparecer en el catálogo del socio.
Investigado antes de implementar si el filtro debía ir en backend o
frontend: se optó por backend, igual que el filtro de sede ya existente en
el mismo endpoint, por eficiencia (evita traer y descartar en el cliente
clases que nunca se van a mostrar) y por consistencia arquitectónica. Como
la regla depende solo de `fecha_hora` (una clase de una semana anterior no
debe verse tenga o no reserva), no hace falta que el filtro conozca las
reservas del socio: basta con acotar `GET /clases` a
`fecha_hora >= inicio de la semana actual (lunes 00:00 UTC)` cuando
`usuario.rol == "socio"`.
Cambiado en `backend/app/modules/clases/router.py` (`listar_clases`): dentro
del mismo bloque `elif usuario.rol == "socio":` que ya aplicaba el filtro de
sede, se añade `Clase.fecha_hora >= inicio_semana_actual`, calculado como
`datetime.combine(ahora.date() - timedelta(days=ahora.weekday()),
datetime.min.time())` (convención `datetime.utcnow()` naive UTC ya usada en
el resto del módulo). El filtro está dentro del bloque específico de
`socio`, por lo que `admin`, `gestor_sede` y `entrenador` no se ven
afectados y siguen viendo el histórico completo, igual que con el filtro de
sede.
**Confirmado explícitamente: este cambio es solo un filtro de lectura sobre
la consulta de listado (`WHERE fecha_hora >= ...`); no se ha borrado,
archivado ni modificado ningún registro de `Clase` ni de `Reserva` en la
base de datos, ni en el código ni durante la verificación manual — los
datos de reservas quedan intactos para facturación, informes y estadísticas
de asistencia.**

Corregido: para una clase pasada con reserva confirmada que seguía siendo
visible (por estar dentro de la semana actual), el botón mostraba
"Reservada · No cancelable (<1h)", un texto pensado solo para una clase que
aún no ha empezado pero está a punto — confuso sobre una clase ya
finalizada. Cambiado en `frontend/src/portal-socio/pages/ClasesPage.jsx`:
cuando `esPasada` es verdadero y el socio tiene una reserva sobre la clase
(confirmada o en lista de espera), el botón pasa a mostrar "Finalizada"
(deshabilitado), igual que ya ocurría para una clase pasada sin reserva; el
resto de la lógica de cancelación (incluida la ventana de 1h de
`HORAS_LIMITE_CANCELACION_CONFIRMADA`) no cambia para clases aún no
iniciadas.

Verificado con 3 tests nuevos en `backend/tests/modules/test_clases.py`
(`test_socio_ve_clase_pasada_de_la_semana_actual_con_reserva`,
`test_socio_no_ve_clase_de_semana_anterior_aunque_tenga_reserva`,
`test_admin_y_gestor_sede_siguen_viendo_historico_completo`) y con una
comprobación manual end-to-end contra datos reales de la BD de desarrollo
(script que crea sobre "Sede Smoke" una clase pasada dentro de la semana
actual y otra de la semana anterior, ambas con reserva confirmada del mismo
socio de prueba): el socio vio la clase de la semana actual pero no la de
la semana anterior, mientras que un admin vio ambas; datos de prueba
(clases, reservas, socio, entrenador, usuarios) eliminados al terminar y
confirmado sin residuos. Lint (`oxlint`) sin errores en el archivo
modificado. Resto de la suite backend: 236 pasan, 2 fallan (los mismos
intermitentes ya documentados en "Pendientes", sin relación con este
cambio).

## 2026-08-18 — Portal de socio: catálogo de clases agrupado por día y subtítulo con más contraste
Añadido (módulo 005/015): el catálogo de clases del portal de socio ahora
agrupa las tarjetas en bloques "Hoy", "Mañana" y el resto por fecha concreta
(p.ej. "Viernes, 21 de agosto"), cada grupo ordenado cronológicamente,
en vez de una rejilla plana sin distinción de día. Cambiado en
`frontend/src/portal-socio/pages/ClasesPage.jsx`: nuevas funciones
`claveDia`/`formatearFechaGrupo` y un `useMemo` `grupos` que ordena
`clasesFiltradas` por `fecha_hora` y las reparte en "Hoy"/"Mañana"/resto
usando la fecha local (año-mes-día) de cada clase; el render itera sobre
`grupos` con un encabezado `<h3>` por bloque en vez de mapear directamente
`clasesFiltradas`.

Corregido: el subtítulo del catálogo ("Reserva tu lugar en las sesiones...")
usaba la clase Tailwind `text-secondary`, que en este proyecto resuelve a
`--color-secondary` — un token registrado dos veces en el mismo bloque
`@theme` de `frontend/src/index.css` (una vez con el gris propio de
portal-socio en la línea 22, y otra con el azul-violeta `#4648d4` reservado
para panel-admin en la línea 55); al estar en el mismo `@theme` sin scoping,
la segunda declaración pisaba la primera para toda la app, dejando el
subtítulo en azul oscuro sobre fondo casi negro con muy poco contraste. En
vez de tocar el token compartido (afectaría también a panel-admin, fuera de
alcance), se cambió el subtítulo y la fecha/duración de cada tarjeta de
`text-secondary` a `text-on-surface-variant` (`#c4c9ac`, ya usado en el
resto del catálogo para texto secundario sobre fondo oscuro), que sí es un
token propio de portal-socio sin colisión.
Contraste verificado por cálculo de luminancia relativa WCAG 2.x de
`#c4c9ac` sobre el fondo `#131313`: ratio ≈ 10.88:1, muy por encima del
mínimo 4.5:1 (AA, texto normal) pedido.
Verificado con una comprobación manual end-to-end contra datos reales de la
BD de desarrollo (script que crea 3 clases temporales — hoy, mañana y +5
días — sobre "Sede Smoke", llama a `GET /clases` como socio y reproduce en
Python la misma lógica de agrupado que `ClasesPage.jsx`): las 3 clases
aparecieron correctamente repartidas en los grupos "Hoy", "Mañana" y la
fecha concreta posterior, en orden cronológico dentro de cada grupo; datos
de prueba eliminados al terminar.

## 2026-08-18 — Reservas de clases: no se puede cancelar una plaza confirmada a <1h del inicio
Añadido: regla de negocio de módulo 005 — un socio no puede cancelar una
reserva **confirmada** (plaza ya ocupada) si queda menos de 1 hora para que
empiece la clase. Esta restricción no aplica a salir de la lista de espera:
un socio en lista de espera no ocupa ninguna plaza, así que puede quitarse
de la cola en cualquier momento, incluso a menos de 1h del inicio. Un socio
promocionado automáticamente desde la lista de espera pasa a tener una
reserva confirmada y a partir de ahí le aplica la misma regla de 1h.
Cambiado en `backend/app/modules/clases/service.py`: nueva constante
`HORAS_LIMITE_CANCELACION_CONFIRMADA = 1`, pensada para hacerse
configurable desde el módulo 014 más adelante (sin implementar esa
configurabilidad todavía). En `backend/app/modules/clases/router.py`,
`DELETE /reservas/{reserva_id}` rechaza con 409 la cancelación cuando
`reserva.estado == "confirmada"` y falta menos de esa ventana para
`clase.fecha_hora`; si `reserva.estado == "lista_espera"` no se aplica
ningún límite de tiempo.
En el frontend (`ClasesPage.jsx` del portal de socio), el botón "Cancelar"
de una reserva confirmada se deshabilita visualmente cuando falte menos de
1h, con un tooltip explicando el motivo; el botón de salir de la lista de
espera no se ve afectado.
Verificado con 3 tests nuevos en `backend/tests/modules/test_clases.py`
(cancelar confirmada <1h → rechazado, cancelar confirmada >1h → permitido,
salir de lista de espera <1h → permitido) y con una comprobación manual
end-to-end contra datos reales de la BD de desarrollo (clase creada a 30
min del inicio: reserva confirmada no cancelable, salida de lista de
espera de otro socio en la misma clase sí permitida). Se ajustó también
`test_cancelar_fuera_de_plazo_queda_registrado`, que usaba una clase a 30
min del inicio para probar el flag `cancelada_fuera_plazo` (ventana de 120
min, comportamiento no relacionado): pasa a usar 90 min para no chocar con
el nuevo límite de 1h de esta regla.
Resto de la suite backend: 233 pasan, 2 fallan (los mismos intermitentes ya
documentados en "Pendientes", sin relación con este cambio).

## 2026-08-18 — Portal de socio: catálogo de clases exponía y permitía reservar clases de otras sedes
Corregido: `GET /clases` devolvía las clases de todas las sedes sin ninguna
distinción, y un socio podía reservar una clase de una sede distinta a la
suya llamando directamente a la API (aunque el frontend no la mostrara).
Regla de negocio aplicada: un socio solo debe ver y poder reservar las
clases de su propia sede (`Socio.sede_id`, columna obligatoria y siempre
presente para un socio activo — confirmado en el modelo). El filtrado se
aplica en el backend, no en el frontend, para no exponer en la respuesta
de la API datos de clases de otras sedes; el panel admin sigue usando el
mismo endpoint sin restricción, ya que el filtrado nuevo solo se activa
para `usuario.rol == "socio"`.
Cambiado en `backend/app/modules/clases/router.py`:
- `GET /clases`: para un socio, se fuerza `Clase.sede_id == socio.sede_id`
  además de cualquier filtro `sede_id` que se pida explícitamente (nunca
  puede ver otra sede, ni pidiéndola a propósito).
- `GET /clases/{clase_id}`: rechaza con 403 el acceso directo por ID a una
  clase de otra sede.
- `POST /clases/{clase_id}/reservar`: rechaza con 403 la reserva si la
  clase no pertenece a la sede del socio (defensa en profundidad, cubre
  el caso de un `clase_id` obtenido fuera del catálogo ya filtrado).
Verificado con 3 tests nuevos en `backend/tests/modules/test_clases.py`
(listado, detalle y reserva de clase ajena) y con una comprobación manual
end-to-end contra datos reales de la BD de desarrollo (socio de "Sede
Smoke": solo ve sus 2 clases propias; detalle y reserva de una clase de
"Sede sevilla" devuelven 403 ambos).

## 2026-08-17 — Portal de socio: catálogo de clases mostraba clases pasadas como "No disponible"
Corregido: el catálogo de clases del portal de socio (módulo 005) pintaba
clases con fecha ya pasada mezcladas con las futuras, mostrando a la vez su
contador real de "plazas libres" (ajeno a la fecha) y un botón "No
disponible" — combinación inconsistente para el socio. Causa raíz: `GET
/clases` no filtra por fecha (correcto, ya que el panel admin usa el mismo
endpoint para gestión/histórico), pero el frontend del portal de socio no
aplicaba ningún filtro de fecha antes de listar el catálogo. No era un bug
de aforo, permisos ni de membresía: el backend ya rechazaba correctamente
intentos de reserva sobre clases pasadas (409 "La clase ya ha finalizado").
Cambiado: `ClasesPage.jsx` del portal de socio ahora solo incluye en el
catálogo clases futuras con estado "activa", conservando la visibilidad de
cualquier clase pasada sobre la que el socio ya tenga una reserva (para
poder verla o cancelarla). El texto residual del botón deshabilitado para
el caso borde de una clase que pasa a estar finalizada entre la carga y el
render pasa de "No disponible" a "Finalizada".

## 2026-08-14 — Panel admin: alta de socio por email en vez de UUID
Añadido: endpoint `GET /socios/candidatos-alta` (admin/gestor_sede), que 
devuelve usuarios con rol "socio" activos y sin registro `Socio` asociado, 
con filtro opcional `q` por email. Evita altas duplicadas del mismo usuario.
Cambiado: el modal "Alta de Socio" del panel admin sustituye el campo de 
texto libre "ID de usuario" (UUID pegado a mano) por un buscador con 
autocompletado en vivo por email; el UUID se sigue enviando como 
`usuario_id` al guardar. Aclarado también el label "Contacto de emergencia" 
→ "Nombre del contacto de emergencia" para no confundirlo con un teléfono.

## 2026-08-08 — Módulo 001 (Identidad y Roles)
Corregido: passlib 1.7.4 incompatible con bcrypt 5.0.0 (rompía hash 
de contraseñas). Sustituido CryptContext de passlib por uso directo 
de la librería bcrypt.

## Pendientes (no bloqueantes)
- [ ] Constraints de BD para valores permitidos — mejora de robustez, no urgente
- [ ] Invalidar tokens de reset previos — seguridad menor
- [ ] Validación de membresía duplicada — caso borde
- [ ] Duplicación de patrón de acceso — refactor de limpieza, no funcional
- [ ] Acoplamiento cruzado entre módulos (socios↔entrenadores, sedes→socios, 
      membresías→socios/pagos) saltándose la capa de servicio — revisar 
      modularidad antes de escalar el proyecto
- [ ] Paginación inconsistente en listados (clases, leads, accesos, pagos, 
      remesas) — devuelven todo sin límite
- [ ] Consultas N+1 en cálculos de ocupación (dashboard, informes) y 
      listado de remesas — sustituir por queries agregadas
- [ ] PDFs/Excel exportados en informes no se borran tras servirse — 
      se acumulan en disco
- [x] `DIAS_SEMANA` (entrenamiento/service.py, módulo 007) no acepta variantes con tilde — corregido 2026-08-26 (specs/007 T10, ver entrada de esta fecha)
- [ ] Tipado de salida sin modelo estricto en asistente_ia (BorradorOut.contenido)
- [ ] Fallback de Ollama no cubre errores de parseo JSON (solo errores de red)
- [x] Aislamiento pytest↔servidor de desarrollo (BD compartida causando fallos intermitentes por contaminación cruzada) — corregido 2026-08-26 (specs/018, ver entrada de esta fecha)
- [x] `test_pagos.py::test_socio_descarga_su_propia_factura` (y potencialmente otros tests de facturas) intermitente por colisión de nombre de fichero PDF entre tests (`_siguiente_numero_factura()` no es único entre tests aislados) — corregido de raíz 2026-08-27 (specs/008 T11, ver entrada de esta fecha; ya no solo diagnosticado, ver `specs/018 - Aislamiento de entorno de tests/tasks.md` T5 para el historial)

## 17-08-2026 — 403 intermitente en dashboard KPIs (no reproducible)
Se observó un 403 puntual en GET /dashboard/kpis con juan@gesportium.com que hacía desaparecer también el menú lateral del panel admin. Investigado a fondo (código de autorización, registro en BD, pruebas controladas de 401/403) sin encontrar causa reproducible; no reprodujo ni en incógnito ni en sesión normal tras reintentar. Cerrado como artefacto transitorio de sesión (módulo 017 es implementación muy reciente). Si reaparece, capturar el token exacto del momento del fallo antes de recargar.

- ## Mejoras futuras para el catálogo de clases (portal de socio): 
  mostrar entrenador que imparte cada clase, mostrar aforo total además de plazas libres, confirmación antes
  de cancelar una reserva, aviso visual cuando quedan muy pocas plazas.