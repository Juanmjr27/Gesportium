# Plan 011 — Notificaciones

## Fase 0 — Modelo de datos

**Tabla `notificaciones`**
- id (UUID, PK), usuario_id (FK), tipo (enum), canal (enum: email, push)
- estado (enum: pendiente, enviada, fallida), intentos (int)
- fecha_creacion (datetime), fecha_envio (datetime, nullable)

**Tabla `preferencias_notificacion`**
- usuario_id (FK, PK), marketing_activo (boolean, default true)

## Fase 1 — Contratos de API

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | /notificaciones | propio usuario | Historial |
| PUT | /notificaciones/preferencias | propio usuario | Activar/desactivar marketing |
| POST | /notificaciones/interna | sistema (interno) | Encolar notificación (llamado por otros módulos) |

## Fase 2 — Seguridad
- Endpoint interno no expuesto públicamente
- Reutiliza dependencies.py del 001

## Fase 3 — Estructura de carpetas

\`\`\`
backend/
└── app/
    └── modules/
        └── notificaciones/
            ├── models.py
            ├── schemas.py
            ├── router.py
            └── service.py
\`\`\`

## Fase 4 — Dependencias externas
- `fastapi-mail` (ya usado en módulo 001)