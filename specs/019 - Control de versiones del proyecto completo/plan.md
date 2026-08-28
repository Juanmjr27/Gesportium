# Plan 019 — Control de versiones del proyecto completo

## Contexto técnico actual (antes de este plan)
- `git log --oneline`: `cfea2fb` (Initial commit, solo `LICENSE`), `cb00815`
  (Add backend/ as baseline), y los dos commits de esta sesión para
  specs/018 y specs/008/T11 — todos bajo `backend/`, `CHANGELOG.md` y esos
  dos directorios de `specs/`
- `.gitignore` de raíz ya existe (creado sin trackear junto con `backend/`,
  comiteado en `cb00815`): cubre Python/venv/`.env`/editores/logs/
  `backend/storage/`, pero nada de `frontend/`
- `frontend/.gitignore` ya existe y ya cubre `node_modules/`, `dist/`,
  `dist-ssr/`, `*.local`, logs y ficheros de editor — es el `.gitignore`
  estándar generado por el scaffold de Vite, nunca revisado a la luz de
  este proyecto
- Sin trackear: `frontend/` completo, `bocetos/`, `roadmap/`,
  `specs/001` a `specs/017`, `.claude/`, `.specify/`

## Fase 1 — Investigación previa (bloquea el resto)

### 1.1 — `.gitignore` de raíz
`frontend/.gitignore` (nested) ya excluye `node_modules/`/`dist/` de
`frontend/` para git, por precedencia estándar de git sobre `.gitignore`
anidados — no hace falta duplicarlo para que funcione. Aun así, se añade
también al `.gitignore` de raíz una sección `frontend/` explícita (mismo
patrón que ya existe para `backend/storage/`), para que el `.gitignore` de
raíz sea por sí solo una referencia completa de qué se ignora en todo el
proyecto, sin depender de que quien lea el repo sepa que existe un segundo
`.gitignore` anidado.

Confirmado con `ls -la frontend/`: no hay ningún `.env`/`.env.local` en
frontend (el proyecto no usa variables de entorno en el cliente — todas
las URLs de API están hardcodeadas o vía proxy de Vite, confirmado al no
encontrar ningún `.env*` en `frontend/`), así que no hace falta una regla
extra para eso más allá de la ya genérica `*.local` de
`frontend/.gitignore`.

Encontrados dos ficheros sueltos en `frontend/` (`t13-debug.png`,
`t13-wizard-paso1.png`, capturas de una sesión de debug del wizard de 016,
sin relación con el código fuente): se excluyen explícitamente por nombre
en el `.gitignore` de raíz, con comentario, en vez de comitearlos como
parte de la línea base.

### 1.2 — `.claude/` y `.specify/`: decisión fichero por fichero
Inspeccionado el contenido de ambos directorios antes de decidir (no se
asumió "config compartida" ni "todo es personal" sin mirar):

- **`.claude/skills/*/SKILL.md`** (10 ficheros): plantillas de los
  comandos `/speckit-*` del flujo spec-driven del proyecto. Sin datos
  personales ni rutas de máquina. **Se trackean.**
- **`.claude/settings.json`** y **`.claude/settings.local.json`**: ambos
  son en la práctica el mismo tipo de contenido — listas acumuladas de
  comandos auto-aprobados a lo largo de la sesión, con rutas absolutas de
  esta máquina (`C:\Users\User\...`) y referencias a directorios
  temporales de sesión. `settings.local.json` además contiene un JWT de
  sesión pegado en texto plano (token de prueba usado contra
  `localhost:8000` en verificación manual del dashboard). Ninguno de los
  dos es config de equipo limpia. **Decisión explícita del usuario:
  ignorar ambos** (confirmada antes de escribir este plan) — no se
  trackea ninguno.
- **`.specify/scripts/`, `.specify/templates/`, `.specify/workflows/`,
  `.specify/memory/constitution.md`, `.specify/integration.json`,
  `.specify/integrations/*.manifest.json`, `.specify/init-options.json`**:
  scripts de PowerShell, plantillas y checksums del propio framework
  spec-kit — config limpia del flujo del proyecto, sin datos personales ni
  rutas de máquina. **Se trackean.**
- **`.specify/feature.json`**: puntero de una sola línea al feature activo
  (`{"feature_directory": "specs/003 - Socios"}`, ya desactualizado),
  reescrito por cada script de `speckit` en cada sesión — es estado de
  sesión local, análogo a `.git/HEAD`, no config del proyecto. **Decisión
  explícita del usuario: ignorar.**

### 1.3 — Escaneo de secretos
`grep` amplio (case-insensitive) sobre todo lo que se va a añadir —
`frontend/src`, `frontend/*.json`, `frontend/index.html`,
`frontend/vite.config.js`, `specs/001` a `specs/017` (excluyendo 008 y 018,
ya comiteados), `roadmap/`, y los ficheros de texto de `bocetos/`
(`code.html`, `DESIGN.md`) — con el patrón
`api[_-]?key|secret|password\s*[:=]|passwd|token\s*[:=]|-----BEGIN|BEARER
[A-Za-z0-9._-]{20,}|eyJ...\.eyJ...` (JWT literal).

Resultado: **sin hallazgos reales.** Todas las coincidencias son nombres
de variable/campo legítimos del propio código (`password` como prop de
formulario, `access_token` desestructurado de la respuesta de login,
`accessToken` como variable en memoria del cliente HTTP) o menciones de
diseño en los `plan.md`/`tasks.md` de specs (p. ej. "JWT firmado con clave
secreta en variable de entorno", "clave compartida por cabecera
`X-Totem-Key`") — documentan el mecanismo, no contienen el secreto en sí.
Ningún `.env`/`.env.local` existe fuera de `backend/` (ya cubierto por
`.gitignore` desde `cb00815`). Ningún `-----BEGIN` (clave privada) en
ningún fichero de texto de `bocetos/`.

**Confirmado: no se detuvo la feature, no hay nada sensible que excluir
por este motivo.**

## Fase 2 — Qué se comitea

```
frontend/                          (completo, salvo lo cubierto por .gitignore)
specs/001 - Identidad y Roles/  … specs/017 - Panel de administración/
bocetos/
roadmap/
.claude/skills/
.specify/  (salvo feature.json)
.gitignore                         (actualizado, ver Fase 1.1)
```

Explícitamente excluido (y por qué, ver Fase 1):
- `frontend/node_modules/`, `frontend/dist/` — dependencias/build,
  regenerables, ya cubiertos por `frontend/.gitignore` y ahora también por
  el `.gitignore` de raíz
- `frontend/t13-debug.png`, `frontend/t13-wizard-paso1.png` — capturas de
  debug sueltas, no código fuente
- `.claude/settings.json`, `.claude/settings.local.json` — permisos/config
  local de esta máquina, uno de ellos con un token de sesión
- `.specify/feature.json` — puntero de estado de sesión local

## Fase 3 — Verificación previa al commit
`git status --short` completo en la raíz (no solo `git add` a ciegas) para
confirmar antes de comitear que no se cuela ningún `node_modules/`,
`dist/`, ni ningún fichero de los explícitamente excluidos en Fase 2 —
mismo criterio de disciplina ya aplicado en los commits de specs/018 y
specs/008/T11 de esta sesión.

## Fase 4 — Commit final
Un único commit de línea base para todo lo listado en Fase 2 (a diferencia
de specs/018/specs/008, que sí se separaron en dos commits por ser cambios
de comportamiento independientes: esto es un único evento — "el resto del
proyecto entra bajo control de versiones" — sin partes lógicamente
separables entre sí).

## Fase 5 — Documentación
Entrada en `CHANGELOG.md`, mismo formato que las entradas anteriores.
