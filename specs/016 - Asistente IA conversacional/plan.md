# Plan 016 — Asistente IA conversacional
 
## Fase 0 — Modelo de datos
 
**Tabla `conversaciones_ia`**
- id (UUID, PK), socio_id (FK), fecha_inicio (datetime)
**Tabla `mensajes_ia`**
- id (UUID, PK), conversacion_id (FK), rol (enum: socio, asistente)
- contenido (text), fecha (datetime)
**Tabla `borradores_ia`**
- id (UUID, PK), socio_id (FK), tipo (enum: rutina, plan_nutricional)
- **datos_cuestionario (JSON)** — respuestas estructuradas del wizard 
  (sexo, peso_kg, altura_cm, nivel_actividad_actual/
  restricciones_medicas, dias_disponibles_semana/
  preferencia_alimentaria, equipamiento/comidas_al_dia, 
  objetivo_principal, objetivo_detalle, etc. según `tipo`). Se guarda 
  tal cual se recibe, independiente de `contenido`. Al ser JSON (sin 
  columnas fijas), añadir `sexo` al cuestionario (2026-08-24) no 
  requirió ninguna migración nueva
- contenido (JSON) — borrador generado por el asistente; editable por 
  el entrenador antes de aprobar
- estado (enum: pendiente, aprobado, rechazado)
- entrenador_revisor_id (FK, nullable), fecha_revision (datetime, nullable)
- **motivo_rechazo (text, nullable)** — solo si estado = rechazado
> Nota de naming: `tipo` pasa de `nutricion` a `plan_nutricional` para 
> alinear con los nombres usados en la spec y en el payload del 
> cuestionario.
 
## Fase 1 — Contratos de API
 
| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | /asistente/mensaje | propio socio | Enviar mensaje al chat |
| GET | /asistente/historial | propio socio | Ver conversación |
| POST | /asistente/borrador | propio socio | Solicitar borrador de plan nutricional o rutina. Body = payload completo del wizard (`tipo_borrador` + campos de pasos 1–4 de la spec); el service separa `datos_cuestionario` (se guarda tal cual) de la generación de `contenido` vía Ollama |
| GET | /asistente/borradores-pendientes | entrenador | Ver borradores de sus socios. Respuesta incluye `datos_cuestionario` **y** `contenido` por cada borrador — nunca solo el borrador redactado |
| **PATCH** | **/asistente/borradores/{id}** | **entrenador** | **Editar `contenido` antes de aprobar (flujo "editar y aprobar"). No cambia `estado`** |
| POST | /asistente/borradores/{id}/aprobar | entrenador | Aprobar: llama a `crear_rutina_desde_borrador()` / `crear_plan_nutricional_desde_borrador()` (módulo 007) para mapear `borradores_ia.contenido` (ya editado, si aplica) a un registro real con `origen=ia` y `borrador_id`; si el mapeo falla, la aprobación se rechaza |
| POST | /asistente/borradores/{id}/rechazar | entrenador | Rechazar. Body = `{ "motivo": string, obligatorio }`, se guarda en `motivo_rechazo` y se notifica al socio con ese motivo |
 
**Validaciones del body de `POST /asistente/borrador`** (reflejan la 
spec, se definen en `schemas.py`): `sexo` obligatorio (`masculino` \| 
`femenino` \| `prefiero_no_decirlo`), `peso_kg` 20–300, `altura_cm` 
100–250, `dias_disponibles_semana` 1–7, `comidas_al_dia` 2–6, 
`objetivo_detalle` máx. 280 caracteres, resto de campos de selección 
restringidos a los enums de la spec.
 
**Perfil incompleto (edad faltante):** si el socio llega al paso 1 del 
wizard sin `fecha_nacimiento` en su perfil, el frontend la pide ahí 
mismo y la persiste vía el endpoint de actualización de perfil ya 
existente en `Socio` (003) — no se añade endpoint nuevo en este 
módulo, solo se documenta la dependencia. (Corrección 2026-08-24: el 
Paso 1 solo confirma `edad` y `tipo_membresia` — `sexo` nunca fue un 
dato de perfil, se pide en el Paso 2 como parte del cuestionario, sin 
dependencia de `Socio`.)
 
## Fase 2 — Seguridad
- Reutiliza dependencies.py del 001
- ollama_client.py compartido con módulo 013 (misma conexión local)
- Prompt del sistema incluye instrucción explícita de no dar 
  diagnóstico médico
## Fase 3 — Estructura de carpetas (backend)
 
```
backend/
└── app/
    └── modules/
        └── asistente_ia/
            ├── models.py
            ├── schemas.py   # incluye WizardBorradorRequest con las
            │                # validaciones de rango de la spec
            ├── router.py
            └── service.py
```
 
## Fase 4 — Dependencias externas
- Ollama (ya usado en módulo 013, mismo servicio local)
## Fase 5 — Frontend
 
**Stack confirmado:** React + React Router + Tailwind CSS + Vite (visto 
en `package.json`/`node_modules` del proyecto).
 
**Importante — no se parte de cero:** `AsistentePage.jsx` y 
`BorradoresPendientesPage.jsx` ya existen y están en producción (ver 
`CHANGELOG.md`, entrada 2026-08-23), construidos contra el `BorradorCreate` 
y el `/rechazar` sin `motivo` anteriores a esta actualización de la spec. 
Los cambios de backend de las Fases 0-4 (`WizardBorradorRequest`, `motivo` 
obligatorio en rechazar) **rompen esas dos páginas tal como están hoy** — 
esta fase es una modificación de archivos existentes, no una creación 
desde cero.
 
**Estructura real del proyecto** (confirmada por el changelog, no la 
propuesta genérica de una versión anterior de este plan):
 
```
frontend/
└── src/
    ├── portal-socio/
    │   ├── pages/
    │   │   └── AsistentePage.jsx        # EXISTE — tabs Chat libre | Solicitar un borrador;
    │   │                                 # el formulario tipo+objetivo se sustituye por el wizard
    │   └── components/
    │       └── WizardBorrador/           # NUEVO, dentro de portal-socio
    │           ├── WizardBorrador.jsx     # contenedor: estado, progreso, navegación
    │           ├── PasoTipo.jsx
    │           ├── PasoPerfil.jsx         # confirmación de datos + edición si faltan
    │           ├── PasoDatosFisicos.jsx
    │           ├── PasoPreferencias.jsx
    │           ├── PasoObjetivo.jsx
    │           └── PasoResumen.jsx
    └── panel-admin/
        ├── pages/
        │   └── BorradoresPendientesPage.jsx   # EXISTE — hay que añadirle el panel de
        │                                       # datos_cuestionario y las 3 acciones de revisión
        └── components/
            └── RevisionBorrador/          # NUEVO, dentro de panel-admin
                ├── PanelDatosCuestionario.jsx   # solo lectura
                ├── PanelBorrador.jsx            # editable por el entrenador
                └── AccionesRevision.jsx         # aprobar / editar y aprobar / rechazar + motivo
```
 
Los servicios de API existentes de cada área (portal-socio y panel-admin 
tienen los suyos propios, según el changelog — p.ej. 
`panel-admin/services/entrenamientoService.js`) se amplían con las 
llamadas nuevas de la Fase 1, en vez de crear un `asistenteApi.js` 
centralizado nuevo — mantener la convención ya usada en el proyecto.
 
**Rutas** (ya existen, sin cambios): `/asistente` (socio) y 
`/admin/borradores-ia` (entrenador, gateada a rol `entrenador`).
 
**Validación cliente:** replica los rangos de `WizardBorradorRequest` 
del backend (`peso_kg` 20–300, `altura_cm` 100–250, 
`dias_disponibles_semana` 1–7, `comidas_al_dia` 2–6, 
`objetivo_detalle` máx. 280 caracteres) — no se avanza de paso con un 
campo obligatorio vacío o fuera de rango.
 
## Cambios respecto al plan anterior
- `borradores_ia`: + `datos_cuestionario` (JSON), + `motivo_rechazo` (text)
- `tipo`: `nutricion` → `plan_nutricional`
- Nuevo endpoint `PATCH /asistente/borradores/{id}` (editar antes de aprobar)
- `POST /asistente/borradores/{id}/rechazar` ahora exige `motivo` en el body
- `POST /asistente/borrador` documenta el payload completo del wizard, antes no estaba especificado
- Añadida Fase 5 — Frontend, no existía en el plan anterior
 