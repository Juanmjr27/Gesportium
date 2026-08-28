# Plan 009 — Control de acceso

## Fase 0 — Modelo de datos

**Tabla `accesos`**
- id (UUID, PK), socio_id (FK), sede_id (FK)
- fecha_hora (datetime), tipo (enum: entrada, salida)

## Fase 1 — Contratos de API

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | /accesos/checkin | dispositivo autenticado (tótem) | Registrar entrada |
| GET | /sedes/{id}/aforo-actual | gestor_sede, admin | Aforo en tiempo real |
| GET | /accesos/{socio_id} | propio socio, gestor_sede, admin | Historial |

## Fase 2 — Seguridad
- Autenticación especial de dispositivo (token de tótem, no JWT de 
  usuario) — a definir en detalle en implementación
- Valida membresía (004) antes de insertar acceso

## Fase 3 — Estructura de carpetas

\`\`\`
backend/
└── app/
    └── modules/
        └── accesos/
            ├── models.py
            ├── schemas.py
            ├── router.py
            └── service.py
\`\`\`

## Fase 4 — Dependencias externas
Ninguna nueva