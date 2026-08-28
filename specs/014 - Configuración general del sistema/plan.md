# Plan 014 — Configuración general

## Fase 0 — Modelo de datos

**Tabla `configuracion_global`**
- clave (string, PK), valor (string), tipo (enum: texto, numero, booleano)

**Tabla `historial_configuracion`**
- id (UUID, PK), clave (FK), valor_anterior (string), 
  valor_nuevo (string), autor_id (FK), fecha (datetime)

## Fase 1 — Contratos de API

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | /configuracion | admin | Ver todos los parámetros |
| PUT | /configuracion/{clave} | admin | Editar parámetro |

## Fase 2 — Seguridad
- Reutiliza dependencies.py del 001

## Fase 3 — Estructura de carpetas

\`\`\`
backend/
└── app/
    └── modules/
        └── configuracion/
            ├── models.py
            ├── schemas.py
            ├── router.py
            └── service.py
\`\`\`

## Fase 4 — Dependencias externas
Ninguna nueva