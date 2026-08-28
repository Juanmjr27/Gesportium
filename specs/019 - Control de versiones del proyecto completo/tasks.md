# Tasks 019 — Control de versiones del proyecto completo

- [X] T1 — Investigar y actualizar `.gitignore` de raíz: añadir sección
      `frontend/` (node_modules, dist, dist-ssr, coverage, *.local),
      confirmar que no hay `.env`/`.env.local` en frontend, y excluir por
      nombre las dos capturas de debug sueltas (`t13-debug.png`,
      `t13-wizard-paso1.png`)
      Archivo: `.gitignore`
- [X] T2 — Decidir `.claude/` y `.specify/` fichero por fichero (no en
      bloque): inspeccionar contenido de cada uno, confirmar con el
      usuario lo que no esté claro. Añadir a `.gitignore` lo excluido
      (`.claude/settings.json`, `.claude/settings.local.json`,
      `.specify/feature.json`) con comentario explicando el motivo
      Archivo: `.gitignore`
      Resultado: ver plan.md Fase 1.2 — `.claude/skills/` y el resto de
      `.specify/` (scripts, templates, workflows, memory, integration.json,
      integrations/*.manifest.json, init-options.json) se trackean;
      `.claude/settings.json`, `.claude/settings.local.json` (uno con un
      JWT en texto plano) y `.specify/feature.json` (puntero de sesión) se
      excluyen, decisión confirmada explícitamente por el usuario
- [X] T3 — Escaneo de secretos sobre todo lo que se va a añadir
      (`frontend/src`, ficheros de config de frontend, `specs/001` a
      `specs/017`, `roadmap/`, ficheros de texto de `bocetos/`): grep
      amplio de patrones de clave/secreto/token/contraseña/clave privada
      Verificación: ver plan.md Fase 1.3 — sin hallazgos reales, todas las
      coincidencias son nombres de variable/campo legítimos o menciones de
      diseño en specs, no secretos embebidos
- [X] T4 — Revisión de `git status --short` completo en la raíz antes de
      comitear, para confirmar que no se cuela ningún `node_modules/`,
      `dist/`, ni ninguno de los ficheros excluidos en T1/T2
      Verificación: `git diff --cached --name-only | grep -iE
      "node_modules|dist/|settings\.local\.json|settings\.json|feature\.
      json|t13-debug|t13-wizard"` — sin resultados; 184 entradas en
      `git status --short` antes de comitear, todas `A ` (nuevas) o
      `M .gitignore`, ninguna `??` restante
- [X] T5 — Commit final de línea base: `frontend/` completo,
      `specs/001` a `specs/017`, `bocetos/`, `roadmap/`, `.claude/skills/`,
      `.specify/` (salvo `feature.json`), `.gitignore` actualizado
- [X] T6 — Entrada en `CHANGELOG.md`, mismo formato que las anteriores
