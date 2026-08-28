# Plan 007 — Planes de entrenamiento y nutrición

## Fase 0 — Modelo de datos

**Tabla `rutinas`**
- id (UUID, PK), entrenador_id (FK), socio_id (FK)
- nombre (string), activa (boolean)
- fecha_creacion (date)
- origen (enum: manual, ia — default manual)
- borrador_id (FK a borradores_ia (módulo 016), nullable — solo si origen=ia)

**Tabla `ejercicios_rutina`**
- id (UUID, PK), rutina_id (FK)
- nombre (string), series (int), repeticiones (int)
- dia_semana (enum), descanso_segundos (int)

**Tabla `planes_nutricionales`**
- id (UUID, PK), entrenador_id (FK), socio_id (FK)
- nombre (string), activo (boolean), notas (text)
- origen (enum: manual, ia — default manual)
- borrador_id (FK a borradores_ia (módulo 016), nullable — solo si origen=ia)

**Tabla `cumplimiento_rutina`**
- id (UUID, PK), ejercicio_id (FK), socio_id (FK)
- fecha (date), completado (boolean)

## Fase 1 — Contratos de API

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | /rutinas | entrenador | Crear rutina |
| GET | /rutinas/{socio_id} | entrenador, propio socio | Ver rutinas |
| PUT | /rutinas/{id} | entrenador (propia) | Editar |
| POST | /planes-nutricionales | entrenador | Crear plan |
| GET | /planes-nutricionales/{socio_id} | entrenador, propio socio | Ver planes |
| POST | /rutinas/{id}/completar | propio socio | Marcar cumplimiento |

## Fase 2 — Seguridad
- Reutiliza dependencies.py del módulo 001
- Valida relación entrenador-socio contra socios_asignados (006)
- Expone función interna `crear_rutina_desde_borrador(borrador)` / 
  `crear_plan_nutricional_desde_borrador(borrador)` en `service.py`, 
  como punto de integración sancionado para el módulo 016 al aprobar 
  un borrador. Mapea el JSON libre de `borradores_ia.contenido` 
  (016) a los campos estructurados de `rutinas`/`ejercicios_rutina` 
  o `planes_nutricionales`, validando formato antes de insertar; si 
  el mapeo falla, la aprobación (016) se rechaza con error explícito 
  en vez de crear un registro incompleto. El módulo 016 llama a esta 
  función directamente (no reinvoca el contrato REST), fijando 
  `origen = ia` y `borrador_id`

## Fase 3 — Estructura de carpetas

\`\`\`
backend/
└── app/
    └── modules/
        └── entrenamiento/
            ├── models.py
            ├── schemas.py
            ├── router.py
            └── service.py
\`\`\`

## Fase 4 — Dependencias externas
- Módulo 016 (Asistente IA conversacional): consumidor descendente 
  que crea rutinas/planes vía `crear_rutina_desde_borrador()` / 
  `crear_plan_nutricional_desde_borrador()` tras aprobación humana