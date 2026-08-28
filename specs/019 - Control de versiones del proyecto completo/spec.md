# Spec 019 — Control de versiones del proyecto completo

## Resumen
Backend de infraestructura: el repositorio se inicializó en algún momento
con un `git init` que solo llegó a comitear `LICENSE` (`cfea2fb Initial
commit`). `backend/` se trackeó aparte en esta sesión como línea base
(`cb00815 Add backend/ as baseline`), pero el resto del proyecto —
`frontend/` completo (incluido el código ya dado por "hecho" de todos los
módulos, p. ej. el wizard de 016), el historial completo de specs de 001 a
017, `bocetos/` y `roadmap/` — ha estado sin ninguna protección de control
de versiones hasta ahora: sin historial, sin posibilidad de revertir un
cambio, sin diff revisable.

## Relación con módulos existentes
- No añade funcionalidad de producto: es infraestructura de repositorio,
  transversal a todo el proyecto (igual que specs/018, del mismo tipo de
  hallazgo colateral)
- Se descubrió al comitear los fixes de 007/T10 y 003/T13 de esta sesión:
  al revisar qué quedaba pendiente de trackear se confirmó que solo
  `backend/` estaba bajo git

## Problema observado
`git log` solo tiene dos commits antes de esta feature:
1. `cfea2fb` "Initial commit" — solo `LICENSE`
2. `cb00815` "Add backend/ as baseline" — todo `backend/` de golpe, añadido
   en esta sesión como paso previo al fix de specs/018

`git status --short` en la raíz del proyecto muestra como sin trackear
(`??`): `frontend/`, `bocetos/`, `roadmap/`, `specs/001` a `specs/017`
(specs/018 y specs/008 ya se trackearon al comitear esos dos módulos), y
`.claude/`/`.specify/` (config del flujo spec-driven del proyecto,
pendientes de decisión, ver plan.md).

Efecto práctico: todo el trabajo de frontend de los módulos 001-017
(páginas del portal de socio y del panel admin, wizard de 016, ficha de
socio de 017, etc.) ha existido siempre solo en el disco de esta máquina,
sin ningún commit que lo respalde — un fallo de disco, un `rm -rf`
accidental o un checkout mal hecho lo habría perdido sin posibilidad de
recuperación, y no hay forma de revisar cómo llegó el frontend a su estado
actual ni de revertir un cambio concreto.

## Requisitos funcionales
1. Todo el código fuente del proyecto (frontend completo, specs 001-017,
   bocetos, roadmap) debe quedar bajo control de versiones, en la misma
   línea base ya establecida para backend (mismo repo, misma rama `main`)
2. Antes de comitear, debe existir un `.gitignore` de raíz que cubra los
   artefactos generados y dependencias de `frontend/` (`node_modules/`,
   `dist/`, variables de entorno locales, cachés/logs) — mismo criterio ya
   aplicado a `backend/` (`venv/`, `__pycache__/`, `.env`)
3. Debe hacerse un escaneo de secretos sobre todo lo que se vaya a añadir
   (claves de API, contraseñas, tokens, claves privadas, ficheros `.env` no
   ignorados) antes de comitear, ya que nada fuera de `backend/` ha pasado
   nunca por este filtro
4. La inclusión de `.claude/` y `.specify/` (config del flujo del proyecto)
   se decide explícitamente fichero por fichero, no en bloque, distinguiendo
   config/plantillas compartidas de estado o permisos personales de esta
   máquina

## Criterios de aceptación
- Todo el proyecto queda bajo git salvo lo que se decida excluir
  explícitamente y por qué (ver plan.md, sección de exclusiones)
- `git status --short` tras el commit final no muestra ningún fichero de
  código fuente del proyecto sin trackear ni sin decisión explícita de
  exclusión — solo quedan sin trackear los artefactos cubiertos por
  `.gitignore` (dependencias, builds, config personal)
- El escaneo de secretos no encontró ningún secreto real embebido en lo
  añadido (ver tasks.md para el resultado documentado); si hubiera
  aparecido alguno, esta feature se habría detenido antes de comitear

## Fuera de alcance en esta feature
- Limpiar o reescribir el historial de git ya existente (`cfea2fb`,
  `cb00815`, y los commits de specs/018 y specs/008/T11 de esta sesión) —
  no se toca nada ya comiteado
- Configurar CI/CD, hooks de pre-commit, o cualquier automatización nueva
  sobre el repositorio — solo se resuelve que el código exista bajo
  control de versiones
- Decidir si `.claude/settings.json`/`.claude/settings.local.json` deben
  limpiarse de rutas absolutas de esta máquina para poder trackearse en el
  futuro — por ahora quedan excluidos tal cual (ver plan.md)
