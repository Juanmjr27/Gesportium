# Plan 010 — CRM / Leads

## Fase 0 — Modelo de datos

**Tabla `leads`**
- id (UUID, PK), nombre (string), email (string), telefono (string)
- sede_interes_id (FK), origen (string), estado (enum), 
  comercial_id (FK a usuarios, nullable), fecha_creacion (datetime)

**Tabla `interacciones_lead`**
- id (UUID, PK), lead_id (FK), tipo (enum: llamada, email, visita)
- notas (text), fecha (datetime), autor_id (FK)

## Fase 1 — Contratos de API

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | /leads | público, admin, gestor_sede | Alta (formulario web o manual) |
| GET | /leads | admin, gestor_sede, comercial asignado | Listado filtrado |
| PUT | /leads/{id} | admin, gestor_sede, comercial asignado | Editar estado |
| POST | /leads/{id}/interacciones | comercial asignado | Registrar interacción |
| POST | /leads/{id}/convertir | admin, gestor_sede | Convertir a socio |

## Fase 2 — Seguridad
- Reutiliza dependencies.py del 001
- Conversión valida email único antes de crear Usuario (001)

## Fase 3 — Estructura de carpetas

\`\`\`
backend/
└── app/
    └── modules/
        └── crm/
            ├── models.py
            ├── schemas.py
            ├── router.py
            └── service.py
\`\`\`

## Fase 4 — Dependencias externas
Ninguna nueva